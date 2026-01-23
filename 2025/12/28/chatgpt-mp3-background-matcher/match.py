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
#   python matcher_rocksdb.py /path/to/fingerprints.rocks /path/to/query_audio
#
# Example:
#   python matcher_rocksdb.py ./fingerprints.rocks ./query.wav

DB_DIR = argv[1]
QUERY_FILE = argv[2]
CONFIDENCE_THRESHOLD = 50

CF_TRACKS = "tracks"
CF_FP = "fp"

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

def match(query_hashes):
    db, cf_tracks, cf_fp = open_rocks(DB_DIR)
    try:
        id_to_name = load_id_to_name(cf_tracks)

        offset_counts: Dict[Tuple[int, int], int] = {}

        for h, t_query in query_hashes:
            # Expect int fingerprints (packed u64). If not, attempt best-effort conversion.
            if isinstance(h, (bytes, bytearray, memoryview)):
                hb = _to_bytes(h)
                if len(hb) == 8:
                    fp_prefix = hb
                else:
                    # If someone passed a different byte repr, hash down to 8 bytes
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
    finally:
        try:
            cf_fp.close()
            cf_tracks.close()
            db.close()
        except Exception:
            pass

# ---------------- MM:SS HELPER ----------------

def format_mmss(seconds: float) -> str:
    minutes = int(seconds) // 60
    secs = int(seconds) % 60
    return f"{minutes}:{secs:02d}"

# ---------------- MAIN ----------------

def main():
    print("Fingerprinting query...")
    query_hashes = fingerprint(QUERY_FILE)

    print("Matching...")
    track, score, offset = match(query_hashes)

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
        # If your track name is a relative path, this mpv line should still work
        print('mpv "%s" --start=%s' % (track, mmss))

    if score >= CONFIDENCE_THRESHOLD:
        print("Confidence: HIGH ✅")
    else:
        print("Confidence: LOW ⚠️")

if __name__ == "__main__":
    main()
