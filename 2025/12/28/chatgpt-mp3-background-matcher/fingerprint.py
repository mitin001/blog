import os
import sqlite3
import time
import signal
import threading
import queue
from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED
from multiprocessing import cpu_count
from sys import argv

from base import (
    load_audio,
    suppress_vocals,
    spectrogram,
    find_peaks,
    generate_hashes,
    init_db,
)

# ---------------- CONFIG ----------------

DB_FILE = argv[1]
ALBUM_DIR = argv[2]

MAX_WORKERS = cpu_count()

# More buffering helps if load_audio() or DB writes cause bursts.
MAX_IN_FLIGHT = MAX_WORKERS * 6

FUTURE_TIMEOUT = 300

# DB batching knobs
CHECKPOINT_EVERY_TRACKS = 50
COMMIT_EVERY_TRACKS = 10
FP_ROWS_FLUSH_THRESHOLD = 50_000
INSERT_CHUNK = 2_000  # chunk for building fp rows (memory / speed tradeoff)

AUDIO_EXTS = (".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac")

# ---------------- DATABASE ----------------

def open_db(db_file):
    # Writer thread owns the connection.
    conn = sqlite3.connect(db_file, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA wal_autocheckpoint=1000")
    return conn

def create_indexes_if_needed(db_file, is_new):
    if not is_new:
        return
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_tracks_name ON tracks(name)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_fp_hash ON fingerprints(hash)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_fp_track ON fingerprints(track_id)")
    conn.commit()
    conn.close()

def checkpoint_db(conn, mode="PASSIVE"):
    conn.execute(f"PRAGMA wal_checkpoint({mode})")

# ---------------- WORKER ----------------

def fingerprint_worker(args):
    """
    CPU-only worker.
    NEVER touches the database.
    """
    path, track_name = args

    try:
        y = load_audio(path)
        y = suppress_vocals(y)
        S = spectrogram(y)
        peaks = find_peaks(S)
        hashes = generate_hashes(peaks)
        return track_name, hashes, None
    except Exception as e:
        return track_name, None, str(e)

# ---------------- FILE COLLECTION ----------------

def collect_audio_files(root):
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

# ---------------- DB WRITER THREAD ----------------

_SENTINEL = object()

def db_writer_thread(db_file, result_q, stats, stats_lock):
    conn = open_db(db_file)
    cur = conn.cursor()

    # Build set of already-indexed tracks (fast skip).
    cur.execute("""
        SELECT t.name
        FROM tracks t
        WHERE EXISTS (
            SELECT 1 FROM fingerprints f
            WHERE f.track_id = t.id
        )
    """)
    indexed_tracks = {row[0] for row in cur.fetchall()}

    fp_rows_buffer = []
    tracks_since_commit = 0
    tracks_since_checkpoint = 0

    def flush_buffers():
        nonlocal fp_rows_buffer, tracks_since_commit
        if fp_rows_buffer:
            cur.executemany("INSERT INTO fingerprints VALUES (?, ?, ?)", fp_rows_buffer)
            fp_rows_buffer = []
        conn.commit()
        tracks_since_commit = 0

    try:
        while True:
            item = result_q.get()
            if item is _SENTINEL:
                break

            track_name, hashes, err = item

            if err:
                with stats_lock:
                    stats["failed"] += 1
                print(f"[ERROR] {track_name}: {err}")
                continue

            # Safety net: skip if already indexed (handles races/partial DB situations).
            if track_name in indexed_tracks:
                with stats_lock:
                    stats["skipped"] += 1
                print(f"[SKIP] {track_name}")
                continue

            # Extra safety net: confirm DB-side.
            cur.execute(
                """
                SELECT t.id
                FROM tracks t
                WHERE t.name=?
                  AND EXISTS (
                      SELECT 1 FROM fingerprints f
                      WHERE f.track_id = t.id
                  )
                """,
                (track_name,),
            )
            if cur.fetchone():
                indexed_tracks.add(track_name)
                with stats_lock:
                    stats["skipped"] += 1
                print(f"[SKIP] {track_name}")
                continue

            # Ensure track row exists
            cur.execute("INSERT OR IGNORE INTO tracks(name) VALUES (?)", (track_name,))
            cur.execute("SELECT id FROM tracks WHERE name=?", (track_name,))
            track_id = cur.fetchone()[0]

            # Buffer fingerprint rows for faster batched inserts
            # fingerprints table assumed: (hash, track_id, time)
            # hashes assumed iterable of (h, t)
            for i in range(0, len(hashes), INSERT_CHUNK):
                chunk = hashes[i : i + INSERT_CHUNK]
                fp_rows_buffer.extend((h, track_id, t) for (h, t) in chunk)

                # If buffer is huge, flush sooner to avoid memory bloat
                if len(fp_rows_buffer) >= FP_ROWS_FLUSH_THRESHOLD:
                    flush_buffers()

            indexed_tracks.add(track_name)

            tracks_since_commit += 1
            tracks_since_checkpoint += 1

            with stats_lock:
                stats["completed"] += 1
                completed = stats["completed"]
                total = stats["total"]

            print(f"[OK] {track_name} — {len(hashes)} hashes ({completed}/{total})")

            # Commit periodically for throughput
            if tracks_since_commit >= COMMIT_EVERY_TRACKS:
                flush_buffers()

            # Checkpoint periodically to keep WAL from growing forever
            if tracks_since_checkpoint >= CHECKPOINT_EVERY_TRACKS:
                checkpoint_db(conn)
                tracks_since_checkpoint = 0

    finally:
        # Final flush + truncate checkpoint
        try:
            if fp_rows_buffer:
                cur.executemany("INSERT INTO fingerprints VALUES (?, ?, ?)", fp_rows_buffer)
            conn.commit()
            checkpoint_db(conn, mode="TRUNCATE")
        finally:
            conn.close()

# ---------------- INDEXING ----------------

def index_album():
    all_files = collect_audio_files(ALBUM_DIR)
    total_all = len(all_files)

    # We'll still filter with a DB read to avoid wasted CPU.
    # Do this with a short-lived connection in the main thread.
    conn = sqlite3.connect(DB_FILE, timeout=30)
    cur = conn.cursor()
    cur.execute("""
        SELECT t.name
        FROM tracks t
        WHERE EXISTS (
            SELECT 1 FROM fingerprints f
            WHERE f.track_id = t.id
        )
    """)
    indexed_tracks = {row[0] for row in cur.fetchall()}
    conn.close()

    files = [(p, n) for (p, n) in all_files if n not in indexed_tracks]
    total = len(files)
    print(f"Found {total} audio files (out of {total_all}) to fingerprint")

    # Shared stats
    stats = {"completed": 0, "skipped": 0, "failed": 0, "total": total}
    stats_lock = threading.Lock()

    # Result queue for writer thread
    result_q = queue.Queue(maxsize=MAX_IN_FLIGHT * 2)

    shutdown = False

    def handle_sigint(signum, frame):
        nonlocal shutdown
        shutdown = True
        print("\n[CTRL+C] Stopping new submissions; draining in-flight work, then exiting...")

    signal.signal(signal.SIGINT, handle_sigint)

    writer = threading.Thread(
        target=db_writer_thread,
        args=(DB_FILE, result_q, stats, stats_lock),
        daemon=True,
    )
    writer.start()

    pending = set()
    files_iter = iter(files)

    def submit_one(pool):
        try:
            path, name = next(files_iter)
        except StopIteration:
            return False
        pending.add(pool.submit(fingerprint_worker, (path, name)))
        return True

    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as pool:
        # Prime the pool
        while len(pending) < MAX_IN_FLIGHT and not shutdown:
            if not submit_one(pool):
                break

        while pending:
            if shutdown:
                # Cancel anything not started yet
                for fut in list(pending):
                    fut.cancel()
                # We still need to drain whatever is already running/completing.
                # (wait below will return completed futures)
            done, pending = wait(pending, return_when=FIRST_COMPLETED)

            # Refill immediately to keep workers busy (before doing any slow work).
            if not shutdown:
                while len(pending) < MAX_IN_FLIGHT:
                    if not submit_one(pool):
                        break

            # Push results to DB writer (fast)
            for fut in done:
                if fut.cancelled():
                    continue
                try:
                    track_name, hashes, err = fut.result(timeout=FUTURE_TIMEOUT)
                except Exception as e:
                    with stats_lock:
                        stats["failed"] += 1
                    print(f"[HARD FAIL] {e}")
                    continue

                # This put may block briefly if DB is falling behind, but it’s still
                # far cheaper than doing DB work in the main loop.
                result_q.put((track_name, hashes, err))

            # Optional early exit if shutdown and nothing left to run
            if shutdown and not pending:
                break

    # Tell writer to finish and wait for it
    result_q.put(_SENTINEL)
    writer.join()

    with stats_lock:
        completed = stats["completed"]
        skipped = stats["skipped"]
        failed = stats["failed"]
        total = stats["total"]

    print(
        f"\nDone.\n"
        f"Processed: {completed}\n"
        f"Skipped:   {skipped}\n"
        f"Failed:    {failed}\n"
        f"Total:     {total}"
    )

# ---------------- MAIN ----------------

def main():
    db_existed = os.path.exists(DB_FILE)

    init_db(DB_FILE)
    create_indexes_if_needed(DB_FILE, not db_existed)

    print("Building fingerprint database...")
    start = time.time()
    index_album()
    print(f"Finished in {time.time() - start:.1f}s")

if __name__ == "__main__":
    main()
