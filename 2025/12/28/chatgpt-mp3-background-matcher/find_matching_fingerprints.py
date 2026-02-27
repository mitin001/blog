#!/usr/bin/env python3
"""
find_matching_fingerprints.py

Find track-to-track matches between TWO RocksDB fingerprint databases produced by fingerprint.py.

Core idea (same voting logic as match.py, but DB-vs-DB):
- fp CF keys are: fp_u64(8) + track_id_u64(8) + t1_u32(4)
- For each fingerprint fp_u64, collect postings in DB A and DB B.
- Cross-product postings (usually small) votes for (trackA, trackB, delta=tB-tA).
- For each trackA, pick the (trackB, delta) with the most votes.

Usage:
  python find_matching_fingerprints.py <dbA_dir> <dbB_dir>

Optional:
  --both           also compute best matches for tracks in DB B against DB A (second pass)
  --min-score N    only print matches with score >= N (default: 1)
  --confidence N   show HIGH/LOW based on score >= N (default: 50, like match.py)
  --limit N        only print top N matches from DB A (by score desc)

Tuning (env vars):
  FM_MAX_DELTAS_PER_PAIR   keep at most K deltas per (trackA, trackB) (default 5)
  FM_PROGRESS_EVERY        print progress every N unique fps processed (default 200000)
"""

import os
import sys
import struct
import argparse
from collections import defaultdict, Counter

from rocksdict import Rdict, Options

# Must match the DB layout produced by fingerprint.py / match.py
CF_TRACKS = "tracks"
CF_FP = "fp"

# Must match hop/sr used for t frame -> seconds conversion (match.py)
SR = 22050
HOP = 512


def u64be(x: int) -> bytes:
    return struct.pack(">Q", x)


def load_track_map(cf_tracks) -> dict[int, str]:
    """
    tracks CF layout:
      key=b"n:"+track_name_utf8, value=track_id_u64 (big-endian)
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
    """
    for k in cf.keys(from_key=prefix):
        if isinstance(k, memoryview):
            k = k.tobytes()
        if not k.startswith(prefix):
            break
        yield k


def format_offset_mmss(seconds: float) -> str:
    """Format an offset in seconds as [+/-]mm:ss."""
    sign = "-" if seconds < 0 else ""
    total = int(round(abs(seconds)))
    mm = total // 60
    ss = total % 60
    return f"{sign}{mm:02d}:{ss:02d}"


def parse_fp_key(k: bytes):
    """
    key = fp_u64(8) + track_id_u64(8) + t1_u32(4)
    """
    fp_u64 = struct.unpack(">Q", k[0:8])[0]
    track_id = struct.unpack(">Q", k[8:16])[0]
    t1 = struct.unpack(">I", k[16:20])[0]
    return fp_u64, track_id, t1


def prune_delta_map(delta_map: dict[int, int], keep_k: int):
    """
    Keep only the top-K deltas by count in-place.
    delta_map: {delta -> count}
    """
    if keep_k <= 0:
        return
    if len(delta_map) <= keep_k:
        return
    top = sorted(delta_map.items(), key=lambda kv: kv[1], reverse=True)[:keep_k]
    delta_map.clear()
    delta_map.update(top)


def find_matches_one_direction(
    cf_fp_a,
    track_map_a: dict[int, str],
    cf_fp_b,
    track_map_b: dict[int, str],
    *,
    max_deltas_per_pair: int = 5,
    progress_every: int = 200_000,
):
    """
    Returns:
      best_for_track_a: dict[track_id_a] -> (track_id_b, delta_frames, score)
      plus some stats.
    """
    # votes[trackA][trackB] = {delta_frames: count}
    votes: dict[int, dict[int, dict[int, int]]] = defaultdict(lambda: defaultdict(dict))

    unique_fps = 0
    keys_iter = cf_fp_a.keys()  # ordered by (fp_u64, track_id, t1)

    cur_fp = None
    postings_a: list[tuple[int, int]] = []  # (trackA, tA)

    def process_group(fp_u64: int, group_a: list[tuple[int, int]]):
        nonlocal votes
        prefix = u64be(fp_u64)

        # postings in B for this fingerprint
        postings_b: list[tuple[int, int]] = []
        for kb in iter_keys_with_prefix(cf_fp_b, prefix):
            _, tb, t1b = parse_fp_key(kb)
            postings_b.append((tb, t1b))

        if not postings_b:
            return

        # cross-product vote
        # vote key: (trackA, trackB, delta=tB-tA)
        for ta, t1a in group_a:
            by_track_b = votes[ta]
            for tb, t1b in postings_b:
                delta = t1b - t1a
                dm = by_track_b.get(tb)
                if dm is None:
                    dm = {}
                    by_track_b[tb] = dm
                dm[delta] = dm.get(delta, 0) + 1

                # keep only top K deltas per (trackA, trackB) to cap memory
                if max_deltas_per_pair and len(dm) > max_deltas_per_pair + 2:
                    prune_delta_map(dm, max_deltas_per_pair)

    for k in keys_iter:
        if isinstance(k, memoryview):
            k = k.tobytes()
        if len(k) < 20:
            continue

        fp_u64, track_id_a, t1a = parse_fp_key(k)

        if cur_fp is None:
            cur_fp = fp_u64

        if fp_u64 != cur_fp:
            # process previous fp group
            process_group(cur_fp, postings_a)
            unique_fps += 1
            if progress_every and unique_fps % progress_every == 0:
                print(f"...processed {unique_fps:,} unique fingerprints", file=sys.stderr)

            # reset for new fp
            cur_fp = fp_u64
            postings_a = []

        postings_a.append((track_id_a, t1a))

    # last group
    if cur_fp is not None and postings_a:
        process_group(cur_fp, postings_a)
        unique_fps += 1

    # finalize: choose best (trackB, delta) per trackA by highest count
    best_for_track_a: dict[int, tuple[int, int, int]] = {}  # trackA -> (trackB, delta, score)

    for track_a, by_track_b in votes.items():
        best = None
        best_score = 0
        best_tb = None
        best_delta = None

        for track_b, delta_map in by_track_b.items():
            # choose best delta for this (trackA, trackB)
            if not delta_map:
                continue
            delta, score = max(delta_map.items(), key=lambda kv: kv[1])
            if score > best_score:
                best_score = score
                best_tb = track_b
                best_delta = delta
                best = (track_b, delta, score)

        if best is not None:
            best_for_track_a[track_a] = best

    stats = {
        "unique_fps_processed": unique_fps,
        "tracks_a_with_votes": len(best_for_track_a),
        "tracks_a_total": len(track_map_a),
        "tracks_b_total": len(track_map_b),
    }
    return best_for_track_a, stats


def open_db(db_dir: str):
    opts = Options(raw_mode=True)
    db = Rdict(db_dir, options=opts, column_families={CF_TRACKS: Options(), CF_FP: Options()})
    cf_tracks = db.get_column_family(CF_TRACKS)
    cf_fp = db.get_column_family(CF_FP)
    return db, cf_tracks, cf_fp


def print_results(
    best_for_a: dict[int, tuple[int, int, int]],
    track_map_a: dict[int, str],
    track_map_b: dict[int, str],
    *,
    min_score: int,
    confidence_threshold: int,
    limit: int | None,
    label_a: str,
    label_b: str,
):
    rows = []
    for track_a, (track_b, delta_frames, score) in best_for_a.items():
        if score < min_score:
            continue
        rows.append((score, track_a, track_b, delta_frames))

    rows.sort(reverse=True, key=lambda r: r[0])
    if limit is not None:
        rows = rows[:limit]

    for score, track_a, track_b, delta_frames in rows:
        name_a = track_map_a.get(track_a, "<unknown>")
        name_b = track_map_b.get(track_b, "<unknown>")

        offset_seconds = (delta_frames * HOP) / SR
        offset_mmss = format_offset_mmss(offset_seconds)

        print(f"[MATCH] ({score}) {label_a}:{name_a} -> {label_b}:{name_b} @ {offset_mmss}")
        print('mpv "%s" --start=%s' % (label_b, offset_mmss))

        if score >= confidence_threshold:
            print("Confidence: HIGH ✅")
        else:
            print("Confidence: LOW ⚠️")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("db_a", help="RocksDB dir A (produced by fingerprint.py)")
    ap.add_argument("db_b", help="RocksDB dir B (produced by fingerprint.py)")
    ap.add_argument("--both", action="store_true", help="Also match DB B -> DB A (second pass)")
    ap.add_argument("--min-score", type=int, default=1, help="Only print matches with score >= N")
    ap.add_argument(
        "--confidence",
        type=int,
        default=50,
        help="Score threshold for HIGH confidence (default 50 like match.py)",
    )
    ap.add_argument("--limit", type=int, default=None, help="Only print top N matches (by score desc)")
    args = ap.parse_args()

    max_deltas_per_pair = int(os.getenv("FM_MAX_DELTAS_PER_PAIR", "5"))
    progress_every = int(os.getenv("FM_PROGRESS_EVERY", "200000"))

    dbA, cf_tracks_a, cf_fp_a = open_db(args.db_a)
    dbB, cf_tracks_b, cf_fp_b = open_db(args.db_b)

    try:
        track_map_a = load_track_map(cf_tracks_a)
        track_map_b = load_track_map(cf_tracks_b)

        print(
            f"Loaded DB A tracks: {len(track_map_a)} | DB B tracks: {len(track_map_b)}",
            file=sys.stderr,
        )
        print(
            f"Voting config: max_deltas_per_pair={max_deltas_per_pair}, progress_every={progress_every}",
            file=sys.stderr,
        )

        best_a, stats = find_matches_one_direction(
            cf_fp_a,
            track_map_a,
            cf_fp_b,
            track_map_b,
            max_deltas_per_pair=max_deltas_per_pair,
            progress_every=progress_every,
        )
        print(f"Stats A->B: {stats}", file=sys.stderr)

        print_results(
            best_a,
            track_map_a,
            track_map_b,
            min_score=args.min_score,
            confidence_threshold=args.confidence,
            limit=args.limit,
            label_a="A",
            label_b="B",
        )

        if args.both:
            best_b, stats2 = find_matches_one_direction(
                cf_fp_b,
                track_map_b,
                cf_fp_a,
                track_map_a,
                max_deltas_per_pair=max_deltas_per_pair,
                progress_every=progress_every,
            )
            print(f"Stats B->A: {stats2}", file=sys.stderr)

            print_results(
                best_b,
                track_map_b,
                track_map_a,
                min_score=args.min_score,
                confidence_threshold=args.confidence,
                limit=args.limit,
                label_a="B",
                label_b="A",
            )

    finally:
        try:
            dbA.close()
        except Exception:
            pass
        try:
            dbB.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
