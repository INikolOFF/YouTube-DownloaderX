### YouTube DownloaderX

A simple, cross-platform Python application to download YouTube videos in the highest available quality (up to 4K) using the yt-dlp library. Features both a command-line interface and a Matrix-themed web interface built with vanilla JavaScript.

![Interface Demo](downloaderx_demo.gif)

---

## Technical Stack

### Backend
- **Python 3.x** - Core application logic
- **yt-dlp** - YouTube download engine
- **Flask** - Web server framework
- **FFmpeg** - Media processing and stream merging

### Frontend (Web Interface)
- **Vanilla JavaScript** - No frameworks, pure ES6+
- **HTML5 Canvas** - Matrix rain animation
- **CSS3** - CRT effects, animations, responsive design
- **REST API** - Async fetch for real-time updates

**Design Philosophy:** Zero dependencies frontend - no React, Vue, or jQuery. Pure web standards for maximum compatibility and minimal bundle size.

---

## Prerequisites

1. **Python 3.x:** Ensure Python is installed on your system.

2. **[FFmpeg](https://ffmpeg.org):** Required for merging high-quality video and audio streams.
   - **macOS:** Install via Homebrew: `brew install ffmpeg`
   - **Windows:** Download from ffmpeg.org and add the bin folder to your PATH.

---

## Installation

Install the required libraries using pip:

```bash
pip install yt-dlp flask
```

**Note:** Flask is only required for the web interface. For command-line usage, only `yt-dlp` is needed.

---

## Usage

### Command Line Interface

1. Run the script:
   ```bash
   python main.py
   ```

2. Paste the YouTube URL when prompted (works with both single videos and playlists).

3. Choose your settings:
   - **Archive Mode** - Skip videos already downloaded (tracks by video ID)
   - **Duplicate Detection** - Compare file hashes to detect identical files with different names

4. Choose your download format:
   - **Video (MP4)** - Best quality video with audio
   - **Audio only (MP3)** - Converted to MP3 format (192 kbps)
   - **Audio only (M4A)** - Original audio quality
   - **Audio only (WAV)** - Lossless audio format

5. The file(s) will be saved automatically in your system's **Downloads** folder.
   - Single videos: Saved directly in Downloads
   - Playlists: Saved in a subfolder named after the playlist
   - Duplicate files: You'll be prompted to delete or keep them

---

### Web Interface (Remote Access)

1. Start the web server:
   ```bash
   python web_interface.py
   ```

2. Open your browser and navigate to:
   - **Local access:** `http://localhost:5001`
   - **Remote access:** `http://YOUR_IP:5001` (from another device on the same network)

3. Features:
   - **Live Thumbnail Preview** - See video thumbnail before downloading
   - **Playlist Detection** - Automatically detects playlists and shows exact video count
   - **Smart Mode Selection** - Choose between downloading single video or entire playlist
   - **Custom Format Selector** - Dropdown menu for video/audio format selection
   - **Real-time Progress** - Live progress bar with speed, ETA, and completion percentage
   - **Stop Downloads** - Cancel active downloads with stop button
   - **Download History** - View all completed and failed downloads
   - **Matrix UI Theme** - Retro terminal aesthetic with CRT scanlines and Matrix rain animation

---

## Features

### Core Download Features
- [x] **Best Quality** - Automatically selects the best video and audio streams
- [x] **Cross-Platform** - Works on Windows and macOS by dynamically resolving file paths
- [x] **Auto-Merge** - Uses FFmpeg to provide a single MP4 file for resolutions above 720p
- [x] **Archive Mode** - Keeps track of downloaded videos to avoid duplicates
- [x] **Duplicate Detection** - Compares file hashes (SHA-256) to detect identical files
- [x] **Playlist Support** - Automatically detects and downloads all videos from playlists
- [x] **Smart Playlist Detection** - Shows exact video count and lets you choose single video or full playlist
- [x] **Format Selection** - Choose between video (MP4) or audio-only formats (MP3, M4A, WAV)
- [x] **Real-time Progress Bar** - Visual progress indicator showing download speed, percentage, and ETA
- [x] **Stop Downloads** - Cancel active downloads mid-process

### Web Interface Features
- [x] **Remote Access** - Access downloader from any device via browser
- [x] **Thumbnail Preview** - See video thumbnail before downloading
- [x] **Playlist Counter** - Shows exact number of videos in playlist (e.g., "VIDEOS: 149")
- [x] **Mode Selection Buttons** - Choose between `[DOWNLOAD_SINGLE]` or `[DOWNLOAD_ALL]`
- [x] **Custom Dropdown Menus** - Vanilla JS dropdown for format selection
- [x] **Matrix Terminal Aesthetic** - CRT scanlines, green terminal theme, animated background
- [x] **Canvas Animation** - Real Matrix rain effect (0s and 1s falling)
- [x] **Responsive Design** - Mobile-friendly interface
- [x] **Download History Log** - Track all downloads with timestamps and status

### Technical Features
- [x] **Vanilla JavaScript** - No frameworks, pure ES6+ for maximum compatibility
- [x] **REST API Backend** - Flask endpoints for playlist info, downloads, progress tracking
- [x] **Async Progress Polling** - Real-time updates without page refresh
- [x] **Threaded Downloads** - Non-blocking background downloads
- [x] **Error Handling** - Graceful failure with informative error messages

---

## Planned Features

### Core Enhancements
- [ ] **Live Stream Recorder** - Capture ongoing live streams with automatic reconnection
- [ ] **Resolution Picker** - Let users choose specific quality
- [ ] **Custom Folder Selection** - Choose save location via directory picker
- [ ] **Desktop Notifications** - System alerts when downloads complete

### Processing
- [ ] **Smart Metadata** - Auto-embed thumbnails and media tags
- [ ] **SponsorBlock Integration** - Skip sponsored segments automatically
- [ ] **Trim/Crop Tool** - Download specific time segments

### Platform Support
- [ ] **Multi-Platform** - Support TikTok, Instagram, Twitter, Vimeo
- [ ] **Batch Queue** - Queue multiple URLs for sequential download
- [ ] **System Tray** - Run as background process

### Web Interface
- [ ] **WebSocket Support** - Real-time bidirectional updates
- [ ] **Multiple Downloads** - Concurrent download support
- [ ] **Drag & Drop** - Drag YouTube links onto interface
- [ ] **Export History** - Export as JSON/CSV

---

## Architecture

### Command Line Flow
```
User Input → URL Validation → Playlist Detection → Format Selection
    ↓
Archive Check → Duplicate Detection → yt-dlp Download
    ↓
FFmpeg Merge (if needed) → File Hash Calculation → Save to Downloads
```

### Web Interface Flow
```
Browser Request → Flask Server → REST API Endpoint
    ↓
Background Thread → yt-dlp Download → Progress Updates
    ↓
Async Polling (1s interval) → Update UI → Complete/Error State
```

---

## File Structure

```
YouTube-DownloaderX/
├── main.py                 # CLI interface with duplicate detection
├── web_interface.py        # Flask web server with REST API
├── templates/
│   └── index.html         # Web UI (Vanilla JS, Matrix theme)
├── requirements.txt        # Dependencies (yt-dlp, flask)
└── README.md              # This file
```

---

## Network Configuration

By default, the web interface runs on:
- **Host:** `0.0.0.0` (accessible from network)
- **Port:** `5001` (avoids macOS AirPlay Receiver conflict on port 5000)

To change the port, edit `web_interface.py`:
```python
app.run(host='0.0.0.0', port=YOUR_PORT, debug=True, threaded=True)
```

---

## Troubleshooting

### Port 5000 Already in Use (macOS)
**Issue:** macOS AirPlay Receiver uses port 5000  
**Solution:** The app uses port 5001 by default

### Playlist Count Shows 0
**Issue:** Playlist detection fails  
**Solution:** Ensure URL contains `list=` parameter  
**Example:** `https://youtube.com/watch?v=VIDEO&list=PLAYLIST_ID`

### Web Interface Not Loading
**Issue:** Flask server not running or firewall blocking  
**Solution:**
1. Check Flask terminal for errors
2. Verify port 5001 is not blocked by firewall
3. Use `http://YOUR_IP:5001` not `localhost` from remote devices

### FFmpeg Not Found
**Issue:** FFmpeg not installed or not in PATH  
**Solution:**
- **macOS:** `brew install ffmpeg`
- **Windows:** Download from ffmpeg.org and add to PATH

---

## License

This project is provided as-is for educational purposes.

---

## Credits

- **yt-dlp** - YouTube download engine
- **FFmpeg** - Media processing
- **Flask** - Web framework
- **VT323 Font** - Matrix terminal aesthetic