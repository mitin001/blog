import os
import time
import struct
import hashlib
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from multiprocessing import cpu_count
from sys import argv

import librosa
import numpy as np
from scipy.ndimage import maximum_filter

# ---------------- CONFIG ----------------
# Usage:
#   python fingerprint_rocksdb.py /path/to/db_dir /path/to/album_dir
#
# Example:
#   python fingerprint_rocksdb.py ./fingerprints.rocks ./music_album

DB_DIR = argv[1]
ALBUM_DIR = argv[2]

MAX_WORKERS = cpu_count()
MAX_IN_FLIGHT = MAX_WORKERS * 4
FUTURE_TIMEOUT = 300  # seconds per file

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
    y, _ = librosa.load(path, sr=SR, mono=True)
    return y

def suppress_vocals(y: np.ndarray) -> np.ndarray:
    """Simple harmonic-percussive separation; harmonic keeps instrumental structure."""
    harmonic, _ = librosa.effects.hpss(y)
    return harmonic

def spectrogram(y: np.ndarray) -> np.ndarray:
    S = np.abs(librosa.stft(y, n_fft=FFT_SIZE, hop_length=HOP))
    return librosa.amplitude_to_db(S, ref=np.max)

# ---------------- PEAKS ----------------

def find_peaks(S: np.ndarray) -> np.ndarray:
    local_max = maximum_filter(S, size=PEAK_NEIGHBORHOOD)
    peaks = (S == local_max) & (S > AMP_MIN)
    return np.argwhere(peaks)

def generate_hashes(peaks: np.ndarray):
    """
    Returns list of (fingerprint_u64, t1_int).
    We pack (f1, f2, dt) into a 64-bit int for compactness.
    """
    peaks = sorted(peaks, key=lambda x: x[1])
    out = []

    # Typical frequency bins with FFT_SIZE=4096 => ~2049 bins => fits in 12 bits.
    # dt is bounded to <= 200 => fits in 9 bits.
    # Pack layout (low bits on the right):
    #   [ f1:12 | f2:12 | dt:9 ] = 33 bits total
    # Stored in u64.
    for i in range(len(peaks)):
        f1, t1 = int(peaks[i][0]), int(peaks[i][1])
        for j in range(1, FAN_VALUE):
            if i + j >= len(peaks):
                break
            f2, t2 = int(peaks[i + j][0]), int(peaks[i + j][1])
            dt = t2 - t1
            if MIN_DT <= dt <= MAX_DT:
                fp = ((f1 & 0xFFF) << (12 + 9)) | ((f2 & 0xFFF) << 9) | (dt & 0x1FF)
                out.append((fp, t1))
    return out

# ---------------- ROCKSDB (rocksdict) ----------------

def stable_track_id_u64(track_name: str) -> int:
    """
    Stable 64-bit track id derived from name.
    Avoids needing a global autoincrement counter under concurrency.
    Collision probability is negligible for typical libraries.
    """
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
class FingerprintResult:
    track_name: str
    track_id_u64: int
    fps: list[tuple[int, int]]  # (fp_u64, t1)
    err: str | None

def open_rocks(db_dir: str):
    """
    Opens RocksDB with two column families using rocksdict in raw (bytes-only) mode.
    """
    from rocksdict import Rdict, Options

    os.makedirs(db_dir, exist_ok=True)

    opt = Options(raw_mode=True)
    opt.create_if_missing(True)
    opt.create_missing_column_families(True)
    # Let RocksDB use more background threads (compaction/flush).
    # (You can tune this further if you want.)
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
    """
    Snapshot existing track names by scanning keys with prefix b"n:".
    """
    existing = set()
    prefix = b"n:"
    # rocksdict iterates keys in order; filter by prefix
    for k in cf_tracks.keys():
        if isinstance(k, memoryview):
            k = k.tobytes()
        if not k.startswith(prefix):
            continue
        existing.add(k[len(prefix):].decode("utf-8", errors="replace"))
    return existing

# ---------------- WORKER ----------------

def fingerprint_worker(path: str, track_name: str) -> FingerprintResult:
    try:
        y = load_audio(path)
        y = suppress_vocals(y)
        S = spectrogram(y)
        peaks = find_peaks(S)
        fps = generate_hashes(peaks)
        tid = stable_track_id_u64(track_name)
        return FingerprintResult(track_name=track_name, track_id_u64=tid, fps=fps, err=None)
    except Exception as e:
        return FingerprintResult(track_name=track_name, track_id_u64=0, fps=[], err=str(e))

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

def insert_track_and_fps(db, cf_tracks, cf_fp, res: FingerprintResult) -> int:
    """
    One atomic write batch:
      - track name -> track_id
      - all fp postings as keys with empty values
    """
    from rocksdict import WriteBatch

    wb = WriteBatch(raw_mode=True)

    # 1) track mapping (id is stable, so overwriting is OK)
    wb.put(track_key(res.track_name), u64be(res.track_id_u64), db.get_column_family_handle(CF_TRACKS))

    # 2) fingerprints
    cf_handle_fp = db.get_column_family_handle(CF_FP)
    empty = b""
    for fp_u64, t1 in res.fps:
        wb.put(fp_key(fp_u64, res.track_id_u64, t1), empty, cf_handle_fp)

    db.write(wb)
    return len(res.fps)

def index_album() -> None:
    db, cf_tracks, cf_fp = open_rocks(DB_DIR)

    existing = load_existing_track_names(cf_tracks)
    scheduled_or_done = set(existing)

    files = collect_audio_files(ALBUM_DIR)
    total = len(files)
    print(f"Found {total} audio files")

    pending = set()
    completed = 0
    skipped = 0
    failed = 0

    files_iter = iter(files)

    # Threaded approach:
    # - librosa/numpy/scipy do lots in native code (often releasing the GIL)
    # - RocksDB supports concurrent writes from multiple threads when each has its own WriteBatch
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
                        count = insert_track_and_fps(db, cf_tracks, cf_fp, res)
                        print(f"[OK] {res.track_name} — {count} hashes ({completed}/{total})")
                    except Exception as e:
                        failed += 1
                        print(f"[DB ERROR] {res.track_name}: {e}")

        except KeyboardInterrupt:
            print("\nCtrl+C — closing DB...")
            # Let threads wind down; RocksDB will flush on close.
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
