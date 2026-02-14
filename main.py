import yt_dlp
import os


def is_playlist(url):
    """Check if the URL is a playlist"""
    ydl_opts = {'quiet': True, 'no_warnings': True, 'extract_flat': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get('_type') == 'playlist'
    except:
        return False


def download_playlist(url, use_archive=True):
    """Download all videos from a playlist"""
    downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")

    # Archive file to track downloaded videos
    archive_file = os.path.join(downloads_dir, "yt_download_archive.txt")

    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': os.path.join(downloads_dir, '%(playlist)s/%(playlist_index)s - %(title)s.%(ext)s'),
        'noplaylist': False,  # Enable playlist download
        'ignoreerrors': True,  # Continue on errors
    }

    if use_archive:
        ydl_opts['download_archive'] = archive_file
        print(f"Archive mode enabled. Tracking downloads in: {archive_file}")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract playlist info first
            print("\n📋 Extracting playlist information...")
            info = ydl.extract_info(url, download=False)

            if info:
                playlist_title = info.get('title', 'Unknown Playlist')
                video_count = len(info.get('entries', []))

                print(f"\n🎬 Playlist: {playlist_title}")
                print(f"📊 Total videos: {video_count}")
                print("-" * 50)

                # Confirm download
                confirm = input(f"\nDownload all {video_count} videos? (y/n): ").strip().lower()
                if confirm != 'y':
                    print("Download cancelled.")
                    return

                # Start downloading
                print("\n⬇️  Starting downloads...\n")
                ydl.download([url])

                print(f"\n✓ Playlist download complete!")
                print(f"📁 Saved to: {os.path.join(downloads_dir, playlist_title)}")

    except Exception as e:
        print(f"\nError downloading playlist: {e}")


def download_video(url, use_archive=True):
    """Download a single video"""
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
    print("YouTube Video Downloader (with Playlist & Archive Support)")
    print("=" * 60)

    link = input("Enter YouTube URL (video or playlist): ").strip()

    if link:
        # Ask user if they want to use archive mode
        use_archive_input = input("Enable archive mode to skip duplicates? (y/n): ").strip().lower()
        use_archive = use_archive_input != 'n'

        # Detect if URL is a playlist
        print("\n🔍 Analyzing URL...")
        if is_playlist(link):
            print("✓ Playlist detected!")
            download_playlist(link, use_archive)
        else:
            print("✓ Single video detected!")
            download_video(link, use_archive)
    else:
        print("No URL provided.")