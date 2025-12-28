# [MP3 Background Matcher](https://chatgpt.com/share/6951aa23-34b4-8011-89f1-266f2588a7ff)

This conversation with [ChatGPT](../../../2025/12/28/chatbots.md) answered a question about Shazam-style reverse audio search with noisy recordings.

## If one takes a fragment of a track from a large music library and records voice over it, how to determine the original track from the recording?

This can be done with two Python scripts: fingerprint.py to compute a database of fingerprints for the library (the directory containing the music files) and match.py to fingerprint the recording and find the closest match to it in the fingerprint database. These scripts rely on three pip dependencies: numpy, scipy, librosa.

```bash
pip3 install numpy scipy librosa
python3 fingerprint.py fingerprints.db library
python3 match.py fingerprints.db recording.mp3
```

Because both fingerprint.py and match.py compute fingerprints and use a SQLite database for their storage and retrieval, they call many of the same functions, collected in base.py. These scripts are available on [GitHub](https://github.com/mitin001/blog/tree/main/2025/12/28/chatgpt-mp3-background-matcher).
