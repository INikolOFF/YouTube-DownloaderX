# YouTube DownloaderX

![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Web-Flask-lightgrey?logo=flask)
![JS](https://img.shields.io/badge/Frontend-Vanilla%20JS-yellow?logo=javascript)
![Status](https://img.shields.io/badge/status-working-brightgreen)

Basically a wrapper around yt-dlp with duplicate detection and a Matrix-themed web UI because why not.

Download YouTube videos and playlists from the command line or through a browser. Has a Matrix-themed web UI built with vanilla JS — no frameworks.

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

Two files — `main.py` for CLI, `web_interface.py` for Flask. `templates/` folder is for the web UI.

---

## Notes

- Single videos go to `~/Downloads`, playlists get their own subfolder
- Download history in the web UI resets when you stop the server
- Duplicate detection only runs for single video downloads — hashing a whole playlist takes too long
- Save folder is hardcoded to `~/Downloads` — to change it you have to edit the code directly

---

## Known issues

- Large playlists take a while before downloading starts — it needs to fetch the video count first and there's no clean way around it without downloading blind
- If yt-dlp sanitizes the title differently than I do, the duplicate check will miss the file. Haven't found a clean fix for this yet