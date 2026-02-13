Gemini said
### YouTube DownloaderX
A simple, cross-platform Python script to download YouTube videos in the highest available quality (up to 4K) using the yt-dlp library.

**Prerequisites**

1. **Python 3.x:** Ensure Python is installed on your system.

2. [**FFmpeg:**](https://ffmpeg.org) Required for merging high-quality video and audio streams.

*  **macOS:** Install via Homebrew: ``` brew install ffmpeg ```

*  **Windows:** Download from ffmpeg.org and add the bin folder to your PATH.

**Installation**

Install the required library using pip:

```bash
pip install yt-dlp 
```
### Usage

1. Run the script:
```bash
python main.py
 ```
2. Paste the YouTube URL when prompted.

3. The video will be saved automatically in your system's **Downloads** folder.

**Features** 

*  **Best Quality:** Automatically selects the best video and audio streams.

*  **Cross-Platform:** Works on Windows and macOS by dynamically resolving file paths.

*  **Auto-Merge:** Uses FFmpeg to provide a single MP4 file for resolutions above 720p.
********************************************************************************************
##  Planned Features

### Core Download Features
- [ ] **Archive Mode**: Keep a history of downloaded video IDs to avoid duplicates.
- [ ] **Playlist Support**: Automatically detect and download all videos from a playlist link.
- [ ] **Batch Processing**: Logic to read and download a list of URLs from a text file.
- [ ] **Real-time Progress Bar**: Display download speed, percentage, and ETA in the terminal.
- [ ] **Duplicate Detection**: Compare video hashes and file fingerprints to prevent redundant downloads.
- [ ] **Live Stream Recorder**: Capture ongoing live streams with automatic reconnection on interruption.

### Quality & Format Options
- [ ] **Resolution Picker**: Extract available formats to let users choose specific quality.
- [ ] **Smart Metadata**: Automatically embed thumbnails and media tags into the final file.
- [ ] **Trim/Crop Tool**: Download only specific time segments using FFmpeg parameters.

### Content Management
- [ ] **Custom Folder Selection**: Choose the save location via a system directory picker.
- [ ] **Desktop Notifications**: System-level alerts when a download task is completed.
- [ ] **Cloud Sync (Direct Upload)**: Automated uploading to Google Drive or Dropbox.

### Audio & Video Processing
- [ ] **Noise Reduction**: Apply audio filtering to reduce background noise in downloaded videos.
- [ ] **SponsorBlock**: Integrate API to identify and skip sponsored segments.

### Platform & Integration
- [ ] **Multi-Platform Support**: Extend functionality to support TikTok, Instagram, Twitter, and Vimeo downloads.
- [ ] **Automatic Updates**: Scripted check to ensure dependencies are always up to date.
- [ ] **Remote Web Interface**: A web-based dashboard for remote download management.
- [ ] **System Tray Minimization**: Allow the application to run as a background process.