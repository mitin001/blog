import os
import time
import struct
import hashlib
import gc
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from multiprocessing import cpu_count
from sys import argv

import librosa
import numpy as np
from scipy.ndimage import maximum_filter

# ---------------- CONFIG ----------------
# Usage:
#   python fingerprint.py /path/to/db_dir /path/to/album_dir
#
# Example:
#   python fingerprint.py ./fingerprints.rocks ./music_album

DB_DIR = argv[1]
ALBUM_DIR = argv[2]

# IMPORTANT: Spectrograms / peak maps can be large; too much concurrency will exhaust RAM.
# Defaults are intentionally conservative; override with env vars if you *know* you have plenty of memory.
DEFAULT_MAX_WORKERS = max(1, min(cpu_count(), int(os.getenv("FP_MAX_WORKERS", "4"))))
MAX_WORKERS = int(os.getenv("FP_MAX_WORKERS", str(DEFAULT_MAX_WORKERS)))

# Keep in-flight tasks low to cap peak RAM (each task may hold a full spectrogram briefly).
DEFAULT_MAX_IN_FLIGHT = max(1, min(MAX_WORKERS, int(os.getenv("FP_MAX_IN_FLIGHT", str(MAX_WORKERS)))))
MAX_IN_FLIGHT = int(os.getenv("FP_MAX_IN_FLIGHT", str(DEFAULT_MAX_IN_FLIGHT)))

FUTURE_TIMEOUT = int(os.getenv("FP_FUTURE_TIMEOUT", "300"))  # seconds per file

# Chunk size for RocksDB batched writes. Smaller uses less memory, larger is faster.
FP_WRITE_BATCH = int(os.getenv("FP_WRITE_BATCH", "50000"))

AUDIO_EXTS = (".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac")

SR = 22050
FFT_SIZE = 4096
HOP = 512

PEAK_NEIGHBORHOOD = 20
AMP_MIN = -35  # dB
FAN_VALUE = 15
MIN_DT = 1
MAX_DT = 200

# RocksDB column families
CF_TRACKS = "tracks"
CF_FP = "fp"

# ---------------- AUDIO ----------------

def load_audio(path: str) -> np.ndarray:
    # librosa.load returns float32 by default; keep it that way for memory.
    y, _ = librosa.load(path, sr=SR, mono=True)
    return y

def suppress_vocals(y: np.ndarray) -> np.ndarray:
    """Simple harmonic-percussive separation; harmonic keeps instrumental structure."""
    harmonic, _ = librosa.effects.hpss(y)
    return harmonic

def spectrogram_db(y: np.ndarray) -> np.ndarray:
    S = np.abs(librosa.stft(y, n_fft=FFT_SIZE, hop_length=HOP))
    return librosa.amplitude_to_db(S, ref=np.max)

# ---------------- PEAKS ----------------

def find_peaks(S_db: np.ndarray) -> np.ndarray:
    local_max = maximum_filter(S_db, size=PEAK_NEIGHBORHOOD)
    peaks = (S_db == local_max) & (S_db > AMP_MIN)
    # rows: frequency bin, cols: time frame
    return np.argwhere(peaks)

def iter_hashes_from_peaks(peaks: np.ndarray):
    """
    Yields (fingerprint_u64, t1_int).

    We pack (f1, f2, dt) into a 64-bit int for compactness.

    Peak rows are (f, t). We sort by t to keep locality and reduce random access.
    """
    if peaks.size == 0:
        return
    # Ensure int32 to avoid accidental int64 bloat.
    peaks = np.asarray(peaks, dtype=np.int32)

    # Sort by time (column 1)
    order = np.argsort(peaks[:, 1], kind="mergesort")
    peaks = peaks[order]

    # Layout (low bits on the right):
    #   [ f1:12 | f2:12 | dt:9 ] = 33 bits total
    # Stored in u64.
    n = peaks.shape[0]
    for i in range(n):
        f1 = int(peaks[i, 0])
        t1 = int(peaks[i, 1])
        # pair with the next FAN_VALUE peaks
        lim = min(n, i + FAN_VALUE)
        for j in range(i + 1, lim):
            f2 = int(peaks[j, 0])
            t2 = int(peaks[j, 1])
            dt = t2 - t1
            if MIN_DT <= dt <= MAX_DT:
                fp = ((f1 & 0xFFF) << (12 + 9)) | ((f2 & 0xFFF) << 9) | (dt & 0x1FF)
                yield (fp, t1)

# ---------------- ROCKSDB (rocksdict) ----------------

def stable_track_id_u64(track_name: str) -> int:
    """Stable 64-bit track id derived from name."""
    h = hashlib.blake2b(track_name.encode("utf-8"), digest_size=8).digest()
    return struct.unpack(">Q", h)[0]

def u64be(x: int) -> bytes:
    return struct.pack(">Q", x)

def u32be(x: int) -> bytes:
    return struct.pack(">I", x)

def track_key(track_name: str) -> bytes:
    return b"n:" + track_name.encode("utf-8")

def fp_key(fp_u64: int, track_id_u64: int, t1: int) -> bytes:
    # Prefix is fp_u64 (8 bytes) => efficient prefix scans by fingerprint.
    return u64be(fp_u64) + u64be(track_id_u64) + u32be(t1)

@dataclass(frozen=True)
class PeakResult:
    track_name: str
    track_id_u64: int
    peaks: np.ndarray  # shape (N,2), int32-ish
    err: str | None

def open_rocks(db_dir: str):
    """Opens RocksDB with two column families using rocksdict in raw (bytes-only) mode."""
    from rocksdict import Rdict, Options

    os.makedirs(db_dir, exist_ok=True)

    opt = Options(raw_mode=True)
    opt.create_if_missing(True)
    opt.create_missing_column_families(True)
    # Let RocksDB use more background threads (compaction/flush).
    try:
        opt.set_max_background_jobs(max(4, os.cpu_count() or 4))
    except Exception:
        pass

    # Column family options
    cf_tracks_opt = Options()
    cf_fp_opt = Options()
    # fp keys begin with an 8-byte fingerprint prefix
    try:
        from rocksdict import SliceTransform
        cf_fp_opt.set_prefix_extractor(SliceTransform.create_max_len_prefix(8))
    except Exception:
        pass

    cfs = {CF_TRACKS: cf_tracks_opt, CF_FP: cf_fp_opt}

    db = Rdict(db_dir, options=opt, column_families=cfs)
    cf_tracks = db.get_column_family(CF_TRACKS)
    cf_fp = db.get_column_family(CF_FP)
    return db, cf_tracks, cf_fp

def load_existing_track_names(cf_tracks) -> set[str]:
    """Snapshot existing track names by scanning keys with prefix b"n:"."""
    existing = set()
    prefix = b"n:"
    for k in cf_tracks.keys():
        if isinstance(k, memoryview):
            k = k.tobytes()
        if not k.startswith(prefix):
            continue
        existing.add(k[len(prefix):].decode("utf-8", errors="replace"))
    return existing

# ---------------- WORKER ----------------

def fingerprint_worker(path: str, track_name: str) -> PeakResult:
    """Compute peaks only (not all hashes) to reduce inter-thread memory pressure."""
    try:
        y = load_audio(path)
        y = suppress_vocals(y)
        S_db = spectrogram_db(y)

        # Free the largest intermediate ASAP
        del y

        peaks = find_peaks(S_db)

        # Free spectrogram ASAP (this is usually the biggest array)
        del S_db

        # Tighten dtype to reduce memory carried back to main thread
        peaks = np.asarray(peaks, dtype=np.int32)

        tid = stable_track_id_u64(track_name)

        # Encourage prompt reclamation of temporary arrays in long runs
        gc.collect()

        return PeakResult(track_name=track_name, track_id_u64=tid, peaks=peaks, err=None)
    except Exception as e:
        return PeakResult(track_name=track_name, track_id_u64=0, peaks=np.empty((0, 2), dtype=np.int32), err=str(e))

# ---------------- FILE COLLECTION ----------------

def collect_audio_files(root: str):
    files = []

    if os.path.isfile(root):
        if root.lower().endswith(AUDIO_EXTS):
            return [(root, os.path.basename(root))]
        return []

    for dirpath, _, filenames in os.walk(root):
        for f in filenames:
            if not f.lower().endswith(AUDIO_EXTS):
                continue
            full = os.path.join(dirpath, f)
            rel = os.path.relpath(full, root)
            files.append((full, rel))

    return files

# ---------------- INDEXING ----------------

def write_track_mapping(db, track_name: str, track_id_u64: int) -> None:
    from rocksdict import WriteBatch
    wb = WriteBatch(raw_mode=True)
    wb.put(track_key(track_name), u64be(track_id_u64), db.get_column_family_handle(CF_TRACKS))
    db.write(wb)

def insert_fps_streaming(db, track_id_u64: int, hashes_iter) -> int:
    """Insert fingerprint postings in bounded-memory batches."""
    from rocksdict import WriteBatch

    cf_handle_fp = db.get_column_family_handle(CF_FP)
    empty = b""

    total = 0
    wb = WriteBatch(raw_mode=True)
    in_batch = 0

    for fp_u64, t1 in hashes_iter:
        wb.put(fp_key(fp_u64, track_id_u64, t1), empty, cf_handle_fp)
        in_batch += 1
        total += 1

        if in_batch >= FP_WRITE_BATCH:
            db.write(wb)
            wb = WriteBatch(raw_mode=True)
            in_batch = 0

    if in_batch:
        db.write(wb)

    return total

def index_album() -> None:
    db, cf_tracks, cf_fp = open_rocks(DB_DIR)

    existing = load_existing_track_names(cf_tracks)
    scheduled_or_done = set(existing)

    files = collect_audio_files(ALBUM_DIR)
    total = len(files)
    print(f"Found {total} audio files")
    print(f"Workers: {MAX_WORKERS} | In-flight cap: {MAX_IN_FLIGHT} | FP batch: {FP_WRITE_BATCH}")

    pending = set()
    completed = 0
    skipped = 0
    failed = 0

    files_iter = iter(files)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        try:
            while True:
                while len(pending) < MAX_IN_FLIGHT:
                    try:
                        path, name = next(files_iter)
                    except StopIteration:
                        break

                    if name in scheduled_or_done:
                        skipped += 1
                        completed += 1
                        continue

                    scheduled_or_done.add(name)
                    pending.add(pool.submit(fingerprint_worker, path, name))

                if not pending:
                    break

                done, pending = wait(pending, return_when=FIRST_COMPLETED)

                for fut in done:
                    try:
                        res = fut.result(timeout=FUTURE_TIMEOUT)
                    except Exception as e:
                        failed += 1
                        completed += 1
                        print(f"[HARD FAIL] {e}")
                        continue

                    completed += 1

                    if res.err:
                        failed += 1
                        print(f"[ERROR] {res.track_name}: {res.err}")
                        continue

                    try:
                        # 1) track mapping (id is stable, so overwriting is OK)
                        write_track_mapping(db, res.track_name, res.track_id_u64)

                        # 2) stream hashes into RocksDB in bounded-memory batches
                        count = insert_fps_streaming(db, res.track_id_u64, iter_hashes_from_peaks(res.peaks))

                        print(f"[OK] {res.track_name} — {count} hashes ({completed}/{total})")
                    except Exception as e:
                        failed += 1
                        print(f"[DB ERROR] {res.track_name}: {e}")
                    finally:
                        # Drop large arrays ASAP
                        try:
                            del res
                        except Exception:
                            pass
                        gc.collect()

        except KeyboardInterrupt:
            print("\nCtrl+C — closing DB...")
            raise
        finally:
            try:
                cf_fp.close()
                cf_tracks.close()
                db.close()
            except Exception:
                pass

    print(
        f"\nDone.\n"
        f"Processed: {completed}\n"
        f"Skipped:   {skipped}\n"
        f"Failed:    {failed}\n"
        f"Total:     {total}"
    )

# ---------------- MAIN ----------------

def main():
    print("Building fingerprint database (RocksDB)...")
    start = time.time()
    index_album()
    print(f"Finished in {time.time() - start:.1f}s")

if __name__ == "__main__":
    main()
