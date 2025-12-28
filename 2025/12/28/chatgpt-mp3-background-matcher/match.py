import sqlite3
from sys import argv
from base import load_audio, suppress_vocals, spectrogram, find_peaks, generate_hashes, init_db, HOP, SR

# ---------------- CONFIG ----------------

DB_FILE = argv[1]
QUERY_FILE = argv[2]
CONFIDENCE_THRESHOLD = 50

# ---------------- FINGERPRINT ----------------

def fingerprint(path):
    y = load_audio(path)
    y = suppress_vocals(y)
    S = spectrogram(y)
    peaks = find_peaks(S)
    return generate_hashes(peaks)

# ---------------- MATCHING ----------------

def match(query_hashes):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    offset_counts = {}

    for h, t_query in query_hashes:
        cur.execute("""
            SELECT f.track_id, f.time
            FROM fingerprints f
            WHERE f.hash=?
        """, (h,))

        for track_id, t_db in cur.fetchall():
            offset = int(t_db) - int(t_query)
            key = (track_id, offset)
            offset_counts[key] = offset_counts.get(key, 0) + 1

    if not offset_counts:
        return None, 0, None

    (track_id, best_offset), score = max(
        offset_counts.items(), key=lambda x: x[1]
    )

    cur.execute("SELECT name FROM tracks WHERE id=?", (track_id,))
    track_name = cur.fetchone()[0]

    conn.close()
    return track_name, score, best_offset

# ---------------- MM:SS HELPER ----------------

def format_mmss(seconds):
    minutes = int(seconds) // 60
    secs = int(seconds) % 60
    return f"{minutes}:{secs:02d}"

# ---------------- MAIN ----------------

def main():
    init_db(DB_FILE)

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
        print('mpv "%s" --start=%s' % (track, format_mmss(match_time_sec)))

    if score >= CONFIDENCE_THRESHOLD:
        print("Confidence: HIGH ✅")
    else:
        print("Confidence: LOW ⚠️")

if __name__ == "__main__":
    main()
