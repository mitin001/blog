import os
import sqlite3
from concurrent.futures import ProcessPoolExecutor, as_completed
from sys import argv
from multiprocessing import cpu_count
from base import load_audio, suppress_vocals, spectrogram, find_peaks, generate_hashes, init_db

# ---------------- CONFIG ----------------

DB_FILE = argv[1]
ALBUM_DIR = argv[2]

# ---------------- FINGERPRINT ----------------

def fingerprint_file(args):
    """
    Worker-safe fingerprinting function.
    Returns (track_name, hashes) or None on failure.
    """
    path, track_name = args
    try:
        y = load_audio(path)
        y = suppress_vocals(y)
        S = spectrogram(y)
        peaks = find_peaks(S)
        hashes = generate_hashes(peaks)
        return track_name, hashes
    except Exception as e:
        print(f"[ERROR] {path}: {e}")
        return None

# ---------------- DATABASE ----------------

def get_track_id(cur, track_name):
    cur.execute(
        "INSERT OR IGNORE INTO tracks(name) VALUES (?)",
        (track_name,)
    )
    cur.execute(
        "SELECT id FROM tracks WHERE name=?",
        (track_name,)
    )
    return cur.fetchone()[0]

# ---------------- INDEXING ----------------

def collect_audio_files(root):
    # If root is a file, return it directly
    if os.path.isfile(root):
        return [(root, os.path.basename(root))]

    files = []
    for dirpath, _, filenames in os.walk(root):
        for f in filenames:
            full = os.path.join(dirpath, f)
            rel = os.path.relpath(full, root)
            files.append((full, rel))
    return files

def index_album():
    files = collect_audio_files(ALBUM_DIR)
    print(f"Found {len(files)} files")

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    with ProcessPoolExecutor(max_workers=cpu_count()) as pool:
        futures = {
            pool.submit(fingerprint_file, f): f
            for f in files
        }

        for future in as_completed(futures):
            result = future.result()
            if result is None:
                continue

            track_name, hashes = result
            print(f"Indexing {track_name} ({len(hashes)} hashes)")

            track_id = get_track_id(cur, track_name)
            rows = [(h, track_id, t) for h, t in hashes]

            cur.executemany(
                "INSERT INTO fingerprints VALUES (?, ?, ?)",
                rows
            )

    conn.commit()
    conn.close()

# ---------------- MAIN ----------------

def main():
    init_db(DB_FILE)
    print("Building fingerprint database...")
    index_album()

if __name__ == "__main__":
    main()
