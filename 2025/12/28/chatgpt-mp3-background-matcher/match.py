#!/usr/bin/env python3
"""
match.py

Parallel audio fingerprint matcher for a RocksDB (.rocks) fingerprint database.
Uses THREADS (not processes) to safely utilize all CPU cores without DB locks.

Usage:
  python match.py <db_dir> <query_file_or_dir>
"""

import os
import sys
import struct
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from multiprocessing import cpu_count

import librosa
import numpy as np
from scipy.ndimage import maximum_filter
from rocksdict import Rdict, Options

# ---------------- CONFIG ----------------

AUDIO_EXTS = (".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac")

SR = 22050
FFT_SIZE = 4096
HOP = 512

PEAK_NEIGHBORHOOD = 20
AMP_MIN = -35
FAN_VALUE = 15
MIN_DT = 1
MAX_DT = 200
CONFIDENCE_THRESHOLD = 50

CF_TRACKS = "tracks"
CF_FP = "fp"

# ---------------- AUDIO / FINGERPRINT ----------------

def load_audio(path: str) -> np.ndarray:
    y, _ = librosa.load(path, sr=SR, mono=True)
    return y

def spectrogram(y: np.ndarray) -> np.ndarray:
    S = np.abs(librosa.stft(y, n_fft=FFT_SIZE, hop_length=HOP))
    return librosa.amplitude_to_db(S, ref=np.max)

def find_peaks(S: np.ndarray) -> np.ndarray:
    local_max = maximum_filter(S, size=PEAK_NEIGHBORHOOD)
    return np.argwhere((S == local_max) & (S > AMP_MIN))

def generate_hashes(peaks: np.ndarray):
    peaks = sorted(peaks, key=lambda x: x[1])
    out = []
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

# ---------------- DB / FILE HELPERS ----------------

def u64be(x: int) -> bytes:
    return struct.pack(">Q", x)

def collect_audio_files(path: str):
    if os.path.isfile(path):
        return [path]
    out = []
    for root, _, files in os.walk(path):
        for f in files:
            if f.lower().endswith(AUDIO_EXTS):
                out.append(os.path.join(root, f))
    return out

def load_track_map(cf_tracks) -> dict[int, str]:
    """
    tracks CF layout: key=b"n:"+track_name_utf8, value=track_id_u64 (big-endian)
    """
    mapping: dict[int, str] = {}
    for k, v in cf_tracks.items():
        if isinstance(k, memoryview):
            k = k.tobytes()
        if isinstance(v, memoryview):
            v = v.tobytes()
        if k.startswith(b"n:") and len(v) == 8:
            track_id = struct.unpack(">Q", v)[0]
            mapping[track_id] = k[2:].decode("utf-8", "replace")
    return mapping

def iter_keys_with_prefix(cf, prefix: bytes):
    """
    Iterate keys in `cf` starting at `prefix` and stop once keys no longer match the prefix.

    rocksdict supports:
      - cf.keys(from_key=...)
      - cf.items(from_key=...)

    We use keys() to avoid decoding values.
    """
    for k in cf.keys(from_key=prefix):
        if isinstance(k, memoryview):
            k = k.tobytes()
        # Stop as soon as the ordered keyspace exits the prefix region.
        if not k.startswith(prefix):
            break
        yield k

# ---------------- MATCHING ----------------

def format_offset_mmss(seconds: float) -> str:
    """Format an offset in seconds as [+/-]mm:ss."""
    sign = "-" if seconds < 0 else ""
    total = int(round(abs(seconds)))
    mm = total // 60
    ss = total % 60
    return f"{sign}{mm:02d}:{ss:02d}"


def match_one(path: str, cf_fp, track_map: dict[int, str]):
    """
    fp CF layout:
      key = fp_u64(8) + track_id_u64(8) + t1_u32(4)
      value = b""
    We scan by fp_u64 prefix and vote on (track_id, delta).
    """
    y = load_audio(path)
    S = spectrogram(y)
    peaks = find_peaks(S)
    fps = generate_hashes(peaks)

    votes = Counter()

    for fp_u64, t_query in fps:
        prefix = u64be(fp_u64)
        for k in iter_keys_with_prefix(cf_fp, prefix):
            track_id = struct.unpack(">Q", k[8:16])[0]
            t_db = struct.unpack(">I", k[16:20])[0]
            votes[(track_id, t_db - t_query)] += 1

    if not votes:
        return path, None, 0, None

    (track_id, delta), score = votes.most_common(1)[0]
    # delta is in spectrogram frames; convert to seconds using hop length and sample rate.
    offset_seconds = (delta * HOP) / SR
    offset_mmss = format_offset_mmss(offset_seconds)
    return path, track_map.get(track_id, "<unknown>"), score, offset_mmss

# ---------------- MAIN ----------------

def main():
    if len(sys.argv) != 3:
        print("Usage: match.py <db_dir> <query_file_or_dir>")
        sys.exit(1)

    db_dir, query_path = sys.argv[1], sys.argv[2]

    # IMPORTANT: raw_mode=True because our .rocks DB stores bytes keys/values.
    opts = Options(raw_mode=True)

    # Open DB with explicit column families.
    # (If your DB was created externally, newer rocksdict versions can auto-load CFs;
    # but this explicit form works reliably for DBs created with our indexer.)
    db = Rdict(db_dir, options=opts, column_families={CF_TRACKS: Options(), CF_FP: Options()})
    cf_tracks = db.get_column_family(CF_TRACKS)
    cf_fp = db.get_column_family(CF_FP)

    track_map = load_track_map(cf_tracks)
    files = collect_audio_files(query_path)

    workers = cpu_count()
    print(f"Matching {len(files)} files using {workers} threads...")

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(match_one, f, cf_fp, track_map) for f in files]
        for fut in as_completed(futures):
            path, match, score, offset = fut.result()
            if match:
                print(f"[MATCH] {path} -> {match} @ {offset} ({score})")
                print('mpv "%s" --start=%s' % (match, offset))
                if score >= CONFIDENCE_THRESHOLD:
                    print("Confidence: HIGH ✅")
                else:
                    print("Confidence: LOW ⚠️")
            else:
                print(f"[NO MATCH] {path}")

    db.close()

if __name__ == "__main__":
    main()
