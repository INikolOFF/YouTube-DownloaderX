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