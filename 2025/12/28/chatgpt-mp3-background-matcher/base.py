import sqlite3
import librosa
import numpy as np
from scipy.ndimage import maximum_filter

# ---------------- CONFIG ----------------

SR = 22050
FFT_SIZE = 4096
HOP = 512

PEAK_NEIGHBORHOOD = 20
AMP_MIN = -35  # dB
FAN_VALUE = 15
MIN_DT = 1
MAX_DT = 200

# ---------------- AUDIO ----------------

def load_audio(path):
    y, _ = librosa.load(path, sr=SR, mono=True)
    return y

def suppress_vocals(y):
    """
    Simple harmonic-percussive separation.
    Harmonic keeps instrumental structure.
    """
    harmonic, _ = librosa.effects.hpss(y)
    return harmonic

def spectrogram(y):
    S = np.abs(librosa.stft(y, n_fft=FFT_SIZE, hop_length=HOP))
    return librosa.amplitude_to_db(S, ref=np.max)

# ---------------- PEAKS ----------------

def find_peaks(S):
    local_max = maximum_filter(S, size=PEAK_NEIGHBORHOOD)
    peaks = (S == local_max) & (S > AMP_MIN)
    return np.argwhere(peaks)

def generate_hashes(peaks):
    peaks = sorted(peaks, key=lambda x: x[1])
    hashes = []

    for i in range(len(peaks)):
        f1, t1 = peaks[i]
        for j in range(1, FAN_VALUE):
            if i + j >= len(peaks):
                break

            f2, t2 = peaks[i + j]
            dt = t2 - t1

            if MIN_DT <= dt <= MAX_DT:
                h = f"{f1}|{f2}|{dt}"
                hashes.append((h, int(t1)))

    return hashes

# ---------------- DATABASE ----------------

def init_db(db_file):
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS fingerprints (
            hash TEXT,
            track_id INTEGER,
            time INTEGER,
            FOREIGN KEY(track_id) REFERENCES tracks(id)
        )
    """)

    cur.execute("CREATE INDEX IF NOT EXISTS idx_hash ON fingerprints(hash)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_track ON fingerprints(track_id)")

    conn.commit()
    conn.close()
