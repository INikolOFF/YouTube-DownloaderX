import yt_dlp
import os


def get_format_choice():
    """Ask user to choose download format"""
    print("\n📦 Select download format:")
    print("=" * 50)
    print("1. Video (MP4) - Best quality video + audio")
    print("2. Audio only (MP3) - Converted to MP3")
    print("3. Audio only (M4A) - Original audio quality")
    print("4. Audio only (WAV) - Lossless audio")
    print("-" * 50)

    while True:
        choice = input("Choose format (1-4): ").strip()
        if choice in ['1', '2', '3', '4']:
            return choice
        print("❌ Invalid choice. Please enter 1, 2, 3, or 4.")


def get_format_options(format_choice):
    """Get yt-dlp options based on format choice"""

    if format_choice == '1':
        # Video (MP4)
        return {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'format_name': 'Video (MP4)',
            'icon': '🎬'
        }

    elif format_choice == '2':
        # Audio (MP3)
        return {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'format_name': 'Audio (MP3)',
            'icon': '🎵'
        }

    elif format_choice == '3':
        # Audio (M4A)
        return {
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'm4a',
            }],
            'format_name': 'Audio (M4A)',
            'icon': '🎵'
        }

    elif format_choice == '4':
        # Audio (WAV)
        return {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
            }],
            'format_name': 'Audio (WAV)',
            'icon': '🎵'
        }


def is_playlist(url):
    """Check if the URL is a playlist"""
    ydl_opts = {'quiet': True, 'no_warnings': True, 'extract_flat': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get('_type') == 'playlist'
    except:
        return False


def download_playlist(url, use_archive=True, format_choice='1'):
    """Download all videos from a playlist"""
    downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")

    # Get format options
    format_opts = get_format_options(format_choice)

    # Archive file to track downloaded videos
    archive_file = os.path.join(downloads_dir, "yt_download_archive.txt")

    ydl_opts = {
        'outtmpl': os.path.join(downloads_dir, '%(playlist)s/%(playlist_index)s - %(title)s.%(ext)s'),
        'noplaylist': False,  # Enable playlist download
        'ignoreerrors': True,  # Continue on errors
    }

    # Add format-specific options
    ydl_opts['format'] = format_opts['format']
    if 'postprocessors' in format_opts:
        ydl_opts['postprocessors'] = format_opts['postprocessors']

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
                print(f"📦 Format: {format_opts['format_name']}")
                print("-" * 50)

                # Confirm download
                confirm = input(f"\nDownload all {video_count} items? (y/n): ").strip().lower()
                if confirm != 'y':
                    print("Download cancelled.")
                    return

                # Start downloading
                print(f"\n⬇️  Starting downloads as {format_opts['format_name']}...\n")
                ydl.download([url])

                print(f"\n✓ Playlist download complete!")
                print(f"📁 Saved to: {os.path.join(downloads_dir, playlist_title)}")

    except Exception as e:
        print(f"\nError downloading playlist: {e}")


def download_video(url, use_archive=True, format_choice='1'):
    """Download a single video"""
    # Cross-platform way to target the user's Downloads folder
    downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
    output_template = os.path.join(downloads_dir, "%(title)s.%(ext)s")

    # Get format options
    format_opts = get_format_options(format_choice)

    # Archive file to track downloaded videos
    archive_file = os.path.join(downloads_dir, "yt_download_archive.txt")

    ydl_opts = {
        'format': format_opts['format'],
        'outtmpl': output_template,
        'noplaylist': True,
    }

    # Add postprocessors if needed (for audio conversion)
    if 'postprocessors' in format_opts:
        ydl_opts['postprocessors'] = format_opts['postprocessors']

    # Add archive option if enabled
    if use_archive:
        ydl_opts['download_archive'] = archive_file
        print(f"Archive mode enabled. Tracking downloads in: {archive_file}")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Download file to Downloads folder
            print(f"\n⬇️  Downloading as {format_opts['format_name']}...")
            info = ydl.extract_info(url, download=True)

            # Check if video was actually downloaded or skipped
            if info:
                print(f"\n✓ Download successful: {info.get('title', 'Unknown')}")
                print(f"📦 Format: {format_opts['format_name']}")
    except yt_dlp.utils.DownloadError as e:
        if "has already been recorded in the archive" in str(e):
            print(f"\n⊘ Video already downloaded (found in archive), skipping...")
        else:
            print(f"\nError: {e}")
    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    print("YouTube Downloader X - Video & Audio Downloader")
    print("=" * 60)

    link = input("Enter YouTube URL (video or playlist): ").strip()

    if link:
        # Ask user if they want to use archive mode
        use_archive_input = input("Enable archive mode to skip duplicates? (y/n): ").strip().lower()
        use_archive = use_archive_input != 'n'

        # Ask for format choice
        format_choice = get_format_choice()

        # Detect if URL is a playlist
        print("\n🔍 Analyzing URL...")
        if is_playlist(link):
            print("✓ Playlist detected!")
            download_playlist(link, use_archive, format_choice)
        else:
            print("✓ Single video detected!")
            download_video(link, use_archive, format_choice)
    else:
        print("No URL provided.")