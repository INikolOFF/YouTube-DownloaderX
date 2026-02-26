# YouTube DownloaderX

![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Web-Flask-lightgrey?logo=flask)
![Status](https://img.shields.io/badge/status-working-brightgreen)

Download YouTube videos and playlists from the command line or through a browser. Has a Matrix-themed web UI.

![Demo](downloaderx_demo.gif)

---

## Requirements

- Python 3.x
- FFmpeg (needed for merging video+audio above 720p)

```bash
pip install yt-dlp flask
```

FFmpeg install:
- macOS: `brew install ffmpeg`
- Windows: download from ffmpeg.org and add to PATH

---

## How to run

**Command line:**
```bash
python main.py
```

**Web interface:**
```bash
python web_interface.py
```
Then open `http://localhost:5001` in your browser. From another device on the same network use `http://YOUR_IP:5001`.

> Port 5001 is intentional — macOS uses 5000 for AirPlay

---

## What it does

- Downloads single videos or full playlists
- Formats: MP4 video, MP3 / M4A / WAV audio
- Archive mode — skips already downloaded videos by ID
- Duplicate detection — compares SHA-256 hashes to catch identical files with different names
- Web UI shows thumbnail preview, video count for playlists, live progress, download history

---

## File structure

```
YouTube-DownloaderX/
├── main.py
├── web_interface.py
├── templates/
│   └── index.html
└── README.md
```

---

## Notes

- Single videos go to `~/Downloads`, playlists get their own subfolder
- Download history in the web UI resets when you stop the server
- Duplicate detection only runs for single video downloads — hashing a whole playlist takes too long

---

## Known issues

- Large playlists take a while to get video count before starting
- File path for duplicate check might miss the file if yt-dlp sanitizes the title differently than expected
- No way to change the save folder without editing the code