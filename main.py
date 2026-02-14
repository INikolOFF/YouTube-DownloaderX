import yt_dlp
import os


def download_video(url, use_archive=True):
    # Cross-platform way to target the user's Downloads folder
    downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
    output_template = os.path.join(downloads_dir, "%(title)s.%(ext)s")

    # Archive file to track downloaded videos
    archive_file = os.path.join(downloads_dir, "yt_download_archive.txt")

    ydl_opts = {
        # Select best video with height <= 2160 (4K) + best audio
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': output_template,
        'noplaylist': True,
    }

    # Add archive option if enabled
    if use_archive:
        ydl_opts['download_archive'] = archive_file
        print(f"Archive mode enabled. Tracking downloads in: {archive_file}")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Download file to Downloads folder
            info = ydl.extract_info(url, download=True)

            # Check if video was actually downloaded or skipped
            if info:
                print(f"\n✓ Download successful: {info.get('title', 'Unknown')}")
    except yt_dlp.utils.DownloadError as e:
        if "has already been recorded in the archive" in str(e):
            print(f"\n⊘ Video already downloaded (found in archive), skipping...")
        else:
            print(f"\nError: {e}")
    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    print("YouTube Video Downloader (with Archive Mode)")
    print("-" * 50)

    link = input("Enter YouTube URL: ").strip()

    if link:
        # Ask user if they want to use archive mode
        use_archive_input = input("Enable archive mode to skip duplicates? (y/n): ").strip().lower()
        use_archive = use_archive_input != 'n'

        download_video(link, use_archive)
    else:
        print("No URL provided.")