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

CHECKPOINT_EVERY = 20  # completed files

AUDIO_EXTS = (".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac")

# ---------------- DATABASE ----------------

def open_db(db_file):
    conn = sqlite3.connect(db_file, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA wal_autocheckpoint=1000")
    return conn

def checkpoint_db(db_file, mode="PASSIVE"):
    conn = sqlite3.connect(db_file)
    conn.execute(f"PRAGMA wal_checkpoint({mode})")
    conn.close()

def create_indexes(db_file):
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

# ---------------- WORKER ----------------

def fingerprint_worker(args):
    """
    Fingerprints one audio file unless it already exists in tracks.
    Writes directly to SQLite.
    Returns small status info.
    """
    path, track_name, db_file = args
    conn = open_db(db_file)
    cur = conn.cursor()

    try:
        # --- check if track already exists ---
        cur.execute(
            "SELECT id FROM tracks WHERE name=?",
            (track_name,),
        )
        row = cur.fetchone()
        if row is not None:
            return track_name, 0, "SKIPPED"

        # --- fingerprint ---
        y = load_audio(path)
        y = suppress_vocals(y)
        S = spectrogram(y)
        peaks = find_peaks(S)
        hashes = generate_hashes(peaks)

        # --- insert track ---
        cur.execute(
            "INSERT INTO tracks(name) VALUES (?)",
            (track_name,),
        )
        track_id = cur.lastrowid

        # --- insert fingerprints ---
        cur.executemany(
            "INSERT INTO fingerprints VALUES (?, ?, ?)",
            [(h, track_id, t) for h, t in hashes],
        )

        conn.commit()
        return track_name, len(hashes), None

    except Exception as e:
        conn.rollback()
        return track_name, 0, str(e)

    finally:
        conn.close()

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

# ---------------- INDEXING ----------------

def index_album():
    files = collect_audio_files(ALBUM_DIR)
    total = len(files)

    print(f"Found {total} audio files")

    pending = set()
    completed = 0
    skipped = 0
    failed = 0

    files_iter = iter(files)

    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as pool:
        while True:
            while len(pending) < MAX_IN_FLIGHT:
                try:
                    path, name = next(files_iter)
                except StopIteration:
                    break

                pending.add(
                    pool.submit(
                        fingerprint_worker,
                        (path, name, DB_FILE),
                    )
                )

            if not pending:
                break

            done, pending = wait(
                pending,
                return_when=FIRST_COMPLETED,
            )

            for fut in done:
                try:
                    track, count, status = fut.result(timeout=FUTURE_TIMEOUT)
                except Exception as e:
                    failed += 1
                    print(f"[HARD FAIL] {e}")
                    continue

                completed += 1

                if status == "SKIPPED":
                    skipped += 1
                    print(f"[SKIP] {track}")
                elif status:
                    failed += 1
                    print(f"[ERROR] {track}: {status}")
                else:
                    print(
                        f"[OK] {track} — {count} hashes "
                        f"({completed}/{total})"
                    )

                if completed % CHECKPOINT_EVERY == 0:
                    checkpoint_db(DB_FILE)

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

    if not db_existed:
        print("New database detected — creating indexes...")
        create_indexes(DB_FILE)

    print("Building fingerprint database...")
    start = time.time()
    index_album()
    print(f"Finished in {time.time() - start:.1f}s")

if __name__ == "__main__":
    main()
