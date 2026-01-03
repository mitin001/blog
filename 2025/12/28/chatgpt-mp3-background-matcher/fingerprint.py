import os
import sqlite3
import time
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
MAX_IN_FLIGHT = MAX_WORKERS * 2
FUTURE_TIMEOUT = 300  # seconds per file

# How many successfully-inserted tracks to commit per transaction (tune as needed)
COMMIT_EVERY = 50

AUDIO_EXTS = (".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac")

# ---------------- DATABASE ----------------

def open_db(db_file: str) -> sqlite3.Connection:
    # Single writer connection (main process). Workers should NOT open SQLite.
    conn = sqlite3.connect(db_file, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    # We only require the DB to be consistent at the end (or Ctrl+C), so favor speed.
    # If you prefer more durability, change to NORMAL.
    conn.execute("PRAGMA synchronous=OFF")
    conn.execute("PRAGMA wal_autocheckpoint=1000")
    conn.execute("PRAGMA temp_store=MEMORY")
    # Negative cache_size = KB. Adjust to your RAM budget.
    conn.execute("PRAGMA cache_size=-200000")  # ~200MB
    return conn


def checkpoint_db(db_file: str, mode: str = "PASSIVE") -> None:
    conn = sqlite3.connect(db_file)
    conn.execute(f"PRAGMA wal_checkpoint({mode})")
    conn.close()


def create_indexes(db_file: str) -> None:
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()

    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_fingerprints_hash "
        "ON fingerprints(hash)"
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_fingerprints_track "
        "ON fingerprints(track_id)"
    )
    cur.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_tracks_name "
        "ON tracks(name)"
    )

    conn.commit()
    conn.close()


def load_existing_track_names(conn: sqlite3.Connection) -> set[str]:
    """Snapshot of existing track names at script start."""
    cur = conn.cursor()
    cur.execute("SELECT name FROM tracks")
    return {row[0] for row in cur.fetchall()}


def insert_track_and_hashes(conn: sqlite3.Connection, track_name: str, hashes) -> int:
    """Insert one track + its fingerprints (single-writer). Returns number of hashes inserted."""
    cur = conn.cursor()

    # Safe if the track already exists (unique index on tracks.name).
    cur.execute(
        "INSERT INTO tracks(name) VALUES (?) "
        "ON CONFLICT(name) DO NOTHING",
        (track_name,),
    )

    cur.execute("SELECT id FROM tracks WHERE name=?", (track_name,))
    row = cur.fetchone()
    if row is None:
        raise RuntimeError(f"Could not resolve track id for {track_name}")
    track_id = row[0]

    cur.executemany(
        "INSERT INTO fingerprints VALUES (?, ?, ?)",
        ((h, track_id, t) for (h, t) in hashes),
    )
    return len(hashes)


# ---------------- WORKER ----------------

def fingerprint_worker(args):
    """CPU-only fingerprinting. No SQLite access to avoid lock contention."""
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

def index_album() -> None:
    # Single-writer connection in the main process
    conn = open_db(DB_FILE)

    existing = load_existing_track_names(conn)
    # Prevent duplicate scheduling within this run
    scheduled_or_done = set(existing)

    files = collect_audio_files(ALBUM_DIR)
    total = len(files)
    print(f"Found {total} audio files")

    pending = set()
    completed = 0
    skipped = 0
    failed = 0
    inserted = 0

    files_iter = iter(files)

    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as pool:
        # Batched inserts: one transaction spanning many tracks
        conn.execute("BEGIN")
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
                    pending.add(pool.submit(fingerprint_worker, (path, name)))

                if not pending:
                    break

                done, pending = wait(pending, return_when=FIRST_COMPLETED)

                for fut in done:
                    try:
                        track, hashes, err = fut.result(timeout=FUTURE_TIMEOUT)
                    except Exception as e:
                        failed += 1
                        print(f"[HARD FAIL] {e}")
                        completed += 1
                        continue

                    completed += 1

                    if err:
                        failed += 1
                        print(f"[ERROR] {track}: {err}")
                        continue

                    try:
                        count = insert_track_and_hashes(conn, track, hashes)
                        inserted += 1
                    except Exception as e:
                        failed += 1
                        print(f"[DB ERROR] {track}: {e}")
                        continue

                    print(f"[OK] {track} — {count} hashes ({completed}/{total})")

                    if inserted and (inserted % COMMIT_EVERY == 0):
                        conn.commit()
                        conn.execute("BEGIN")

        except KeyboardInterrupt:
            print("\nCtrl+C — finalizing DB (commit + checkpoint)...")
            pool.shutdown(wait=False, cancel_futures=True)
            try:
                conn.commit()
            finally:
                checkpoint_db(DB_FILE, mode="TRUNCATE")
                conn.close()
            raise
        finally:
            try:
                conn.commit()
            except Exception:
                pass
            conn.close()

    checkpoint_db(DB_FILE, mode="TRUNCATE")

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

    print("Building fingerprint database...")
    start = time.time()
    index_album()

    # For a new DB, build indexes AFTER bulk insert (much faster ingest).
    if not db_existed:
        print("New database detected — creating indexes (post-ingest)...")
        create_indexes(DB_FILE)

    print(f"Finished in {time.time() - start:.1f}s")


if __name__ == "__main__":
    main()
