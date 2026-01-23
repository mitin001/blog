from __future__ import annotations

import os
import struct
from sys import argv
from typing import Dict, Iterable, Iterator, Tuple

from fingerprint import (
    load_audio,
    suppress_vocals,
    spectrogram,
    find_peaks,
    generate_hashes,
    HOP,
    SR,
)

# ---------------- CONFIG ----------------
# Usage:
#   python matcher_rocksdb.py /path/to/fingerprints.rocks /path/to/query_audio_or_dir
#
# Example:
#   python matcher_rocksdb.py ./fingerprints.rocks ./query.wav
#   python matcher_rocksdb.py ./fingerprints.rocks ./queries_dir/

DB_DIR = argv[1]
QUERY_PATH = argv[2]
CONFIDENCE_THRESHOLD = 50

CF_TRACKS = "tracks"
CF_FP = "fp"

AUDIO_EXTS = (".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac")

# ---------------- FINGERPRINT ----------------

def fingerprint(path: str):
    y = load_audio(path)
    y = suppress_vocals(y)
    S = spectrogram(y)
    peaks = find_peaks(S)
    return generate_hashes(peaks)

# ---------------- ROCKSDB HELPERS ----------------

def _to_bytes(x) -> bytes:
    if isinstance(x, bytes):
        return x
    if isinstance(x, memoryview):
        return x.tobytes()
    return bytes(x)

def u64be(x: int) -> bytes:
    return struct.pack(">Q", x)

def open_rocks(db_dir: str):
    """
    Open an existing RocksDB database created by the fingerprinting script.

    Requires:
      pip install rocksdict
    """
    try:
        from rocksdict import Rdict, Options
    except Exception as e:
        raise SystemExit(
            "Missing dependency 'rocksdict'. Install with:\n"
            "  pip install rocksdict\n\n"
            f"Original import error: {e}"
        )

    if not os.path.isdir(db_dir):
        raise SystemExit(f"DB path does not exist or is not a directory: {db_dir}")

    opt = Options(raw_mode=True)
    # Do not silently create a new empty DB by accident.
    try:
        opt.create_if_missing(False)
    except Exception:
        pass

    # Open with the two expected column families.
    # If the DB was created with these CF names, this will succeed.
    db = Rdict(db_dir, options=opt, column_families={CF_TRACKS: Options(), CF_FP: Options()})
    cf_tracks = db.get_column_family(CF_TRACKS)
    cf_fp = db.get_column_family(CF_FP)
    return db, cf_tracks, cf_fp

def iter_prefix(cf, prefix: bytes) -> Iterator[Tuple[bytes, bytes]]:
    """
    Yield (key, value) for all records whose key starts with prefix.
    Tries efficient seek-based iteration first; falls back to full scan if needed.
    """
    # Fast path: seek iteration (API varies by rocksdict version).
    for method_name in ("iter", "iterator", "items"):
        it = getattr(cf, method_name, None)
        if it is None:
            continue

        # Try range iteration forms
        for kwargs in (
                {"from_key": prefix},
                {"start": prefix},
                {"seek": prefix},
                {},
        ):
            try:
                obj = it(**kwargs)  # type: ignore[misc]
            except TypeError:
                continue
            except Exception:
                continue

            try:
                for k, v in obj:
                    k = _to_bytes(k)
                    if not k.startswith(prefix):
                        break
                    yield k, _to_bytes(v)
                return
            except Exception:
                # If the iterator object isn't an iterator of pairs, keep trying.
                pass

    # Slow fallback: full scan
    try:
        for k, v in cf.items():  # type: ignore[attr-defined]
            k = _to_bytes(k)
            if k.startswith(prefix):
                yield k, _to_bytes(v)
    except Exception:
        # Last resort: keys() then get()
        for k in cf.keys():  # type: ignore[attr-defined]
            kb = _to_bytes(k)
            if kb.startswith(prefix):
                yield kb, _to_bytes(cf.get(k))  # type: ignore[attr-defined]

def load_id_to_name(cf_tracks) -> Dict[int, str]:
    """
    Build reverse mapping {track_id_u64: track_name} by scanning tracks CF.
    The fingerprinting DB stores name->id under keys: b"n:" + utf8(name)
    """
    prefix = b"n:"
    out: Dict[int, str] = {}
    try:
        for k, v in iter_prefix(cf_tracks, prefix):
            name = k[len(prefix):].decode("utf-8", errors="replace")
            if len(v) == 8:
                tid = struct.unpack(">Q", v)[0]
                out[tid] = name
    except Exception as e:
        raise SystemExit(f"Failed to read tracks column family: {e}")
    return out


# ---------------- MATCHING ----------------

def parse_fp_key(k: bytes) -> Tuple[int, int, int]:
    """
    Key layout:
      fp_u64(8) + track_id_u64(8) + t_db(4)
    """
    if len(k) < 20:
        raise ValueError(f"Unexpected fp key length: {len(k)}")
    fp = struct.unpack(">Q", k[0:8])[0]
    tid = struct.unpack(">Q", k[8:16])[0]
    t_db = struct.unpack(">I", k[16:20])[0]
    return fp, tid, t_db

def match_hashes(cf_fp, id_to_name: Dict[int, str], query_hashes):
    """
    Match a single query's hashes against the RocksDB fp column family.
    Returns (track_name, score, best_offset_frames).
    """
    offset_counts: Dict[Tuple[int, int], int] = {}

    for h, t_query in query_hashes:
        # Expect int fingerprints (packed u64). If not, attempt best-effort conversion.
        if isinstance(h, (bytes, bytearray, memoryview)):
            hb = _to_bytes(h)
            if len(hb) == 8:
                fp_prefix = hb
            else:
                fp_prefix = struct.pack(">Q", (hash(hb) & ((1 << 64) - 1)))
        else:
            fp_prefix = u64be(int(h))

        for k, _v in iter_prefix(cf_fp, fp_prefix):
            try:
                _fp, track_id, t_db = parse_fp_key(k)
            except Exception:
                continue

            offset = int(t_db) - int(t_query)
            key = (track_id, offset)
            offset_counts[key] = offset_counts.get(key, 0) + 1

    if not offset_counts:
        return None, 0, None

    (track_id, best_offset), score = max(offset_counts.items(), key=lambda x: x[1])
    track_name = id_to_name.get(track_id, f"<unknown track id {track_id}>")

    return track_name, score, best_offset

def collect_audio_files(path: str) -> list[tuple[str, str]]:
    """
    Returns list of (full_path, display_name). If path is a file, list has one item.
    If path is a directory, recurse and collect supported audio extensions.
    """
    if os.path.isfile(path):
        if path.lower().endswith(AUDIO_EXTS):
            return [(path, os.path.basename(path))]
        return []

    out: list[tuple[str, str]] = []
    for dirpath, _, filenames in os.walk(path):
        for f in filenames:
            if not f.lower().endswith(AUDIO_EXTS):
                continue
            full = os.path.join(dirpath, f)
            rel = os.path.relpath(full, path)
            out.append((full, rel))
    return sorted(out, key=lambda x: x[1])

# ---------------- MM:SS HELPER ----------------

def format_mmss(seconds: float) -> str:
    minutes = int(seconds) // 60
    secs = int(seconds) % 60
    return f"{minutes}:{secs:02d}"

# ---------------- MAIN ----------------


def main():
    print("Opening RocksDB...")
    db, cf_tracks, cf_fp = open_rocks(DB_DIR)
    try:
        id_to_name = load_id_to_name(cf_tracks)

        if os.path.isdir(QUERY_PATH):
            files = collect_audio_files(QUERY_PATH)
            if not files:
                raise SystemExit(f"No supported audio files found under: {QUERY_PATH}")

            print(f"Found {len(files)} query files under directory.")
            high = 0

            for full, rel in files:
                print("\n" + "=" * 60)
                print(f"QUERY: {rel}")
                try:
                    q_hashes = fingerprint(full)
                except Exception as e:
                    print(f"[ERROR] Failed to fingerprint {rel}: {e}")
                    continue

                track, score, offset = match_hashes(cf_fp, id_to_name, q_hashes)

                if offset is not None:
                    match_time_sec = offset * HOP / SR
                else:
                    match_time_sec = None

                print("RESULT")
                print("Track:", track)
                print("Score:", score)

                if match_time_sec is not None:
                    mmss = format_mmss(match_time_sec)
                    print(f"Match time: {mmss}")
                    print('mpv "%s" --start=%s' % (track, mmss))

                if score >= CONFIDENCE_THRESHOLD:
                    print("Confidence: HIGH ✅")
                    high += 1
                else:
                    print("Confidence: LOW ⚠️")

            print("\n" + "-" * 60)
            print(f"High-confidence matches: {high}/{len(files)}")
        else:
            print("Fingerprinting query...")
            query_hashes = fingerprint(QUERY_PATH)

            print("Matching (RocksDB)...")
            track, score, offset = match_hashes(cf_fp, id_to_name, query_hashes)

            if offset is not None:
                match_time_sec = offset * HOP / SR
            else:
                match_time_sec = None

            print("RESULT")
            print("Track:", track)
            print("Score:", score)

            if match_time_sec is not None:
                mmss = format_mmss(match_time_sec)
                print(f"Match time: {mmss}")
                print('mpv "%s" --start=%s' % (track, mmss))

            if score >= CONFIDENCE_THRESHOLD:
                print("Confidence: HIGH ✅")
            else:
                print("Confidence: LOW ⚠️")
    finally:
        try:
            cf_fp.close()
            cf_tracks.close()
            db.close()
        except Exception:
            pass

if __name__ == "__main__":
    main()
