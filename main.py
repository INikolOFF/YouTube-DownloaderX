import yt_dlp
import os
import sys
import hashlib
import json


def format_bytes(size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"


def format_speed(speed):
    if speed is None:
        return "Unknown"
    return f"{format_bytes(speed)}/s"


def calculate_file_hash(file_path, algorithm='sha256'):
    hash_func = hashlib.sha256() if algorithm == 'sha256' else hashlib.md5()

    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except Exception as e:
        print(f"Warning: Could not calculate hash for {file_path}: {e}")
        return None


def load_hash_database(db_path):
    if os.path.exists(db_path):
        try:
            with open(db_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load hash database: {e}")
            return {}
    return {}


def save_hash_database(db_path, hash_db):
    try:
        with open(db_path, 'w', encoding='utf-8') as f:
            json.dump(hash_db, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Warning: Could not save hash database: {e}")


def check_duplicate(file_hash, hash_db):
    if file_hash in hash_db:
        return hash_db[file_hash]
    return None


def add_to_hash_database(file_path, file_hash, hash_db, db_path, title=None):
    hash_db[file_hash] = {
        'path': file_path,
        'title': title or os.path.basename(file_path),
        'size': os.path.getsize(file_path) if os.path.exists(file_path) else 0,
        'added': os.path.getctime(file_path) if os.path.exists(file_path) else 0
    }
    save_hash_database(db_path, hash_db)


def sanitize_filename(filename):
    """Remove illegal characters from filename for Windows compatibility"""
    illegal_chars = '<>:"/\\|?*'
    for char in illegal_chars:
        filename = filename.replace(char, '_')
    filename = filename.strip('. ')
    return filename


def progress_hook(d):
    if d['status'] == 'downloading':
        downloaded = d.get('downloaded_bytes', 0)
        total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
        speed = d.get('speed')
        eta = d.get('eta')

        if total > 0:
            percent = (downloaded / total) * 100
            filled_length = int(30 * downloaded // total)
        else:
            percent = 0
            filled_length = 0

        speed_str = format_speed(speed) if speed else "Unknown"
        eta_str = f"{eta}s" if eta else "Unknown"

        bar_length = 30
        bar = '#' * filled_length + '-' * (bar_length - filled_length)

        total_str = format_bytes(total) if total > 0 else "Unknown"

        sys.stdout.write(
            f'\r  [{bar}] {percent:.1f}% | '
            f'{format_bytes(downloaded)}/{total_str} | '
            f'Speed: {speed_str} | ETA: {eta_str}   '
        )
        sys.stdout.flush()

    elif d['status'] == 'finished':
        downloaded = d.get('downloaded_bytes', 0)
        sys.stdout.write(
            f'\r  Download complete: {format_bytes(downloaded)}'
            + ' ' * 50 + '\n'
        )
        sys.stdout.flush()


def get_format_choice():
    print("\nSelect download format:")
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
        print("Invalid choice. Please enter 1, 2, 3, or 4.")


def get_format_options(format_choice):
    if format_choice == '1':
        # Video (MP4)
        return {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'format_name': 'Video (MP4)',
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
        }
    else:
        raise ValueError(f"Invalid format choice: '{format_choice}'. Expected '1', '2', '3', or '4'.")


def is_playlist(url):
    # First check if URL contains playlist parameter
    if 'list=' in url:
        return True

    # Then use yt-dlp to verify
    ydl_opts = {'quiet': True, 'no_warnings': True, 'extract_flat': True, 'socket_timeout': 30}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get('_type') == 'playlist'
    except Exception:
        return False


def ask_playlist_or_video(url):
    print("\nThis URL contains both a video and a playlist!")
    print("=" * 50)
    print("1. Download only this video")
    print("2. Download entire playlist")
    print("-" * 50)

    while True:
        choice = input("Choose option (1-2): ").strip()
        if choice in ['1', '2']:
            return choice
        print("Invalid choice. Please enter 1 or 2.")


class PlaylistStats:
    """Track playlist download statistics"""

    def __init__(self):
        self.total = 0
        self.successful = 0
        self.already_downloaded = 0
        self.errors = []

    def __call__(self, d):
        if d['status'] == 'finished':
            self.successful += 1
        elif d['status'] == 'error':
            self.errors.append(d.get('info_dict', {}).get('title', 'Unknown'))

    def debug(self, msg):
        if 'has already been recorded in the archive' in msg:
            self.already_downloaded += 1

    def warning(self, msg):
        pass

    def error(self, msg):
        pass

    def print_summary(self, playlist_title, playlist_path):
        print("\n" + "=" * 70)
        print("DOWNLOAD STATISTICS")
        print("=" * 70)
        print(f"Playlist : {playlist_title}")
        print(f"Location : {playlist_path}")
        print(f"\nTotal items in playlist : {self.total}")
        print(f"Successfully downloaded : {self.successful}")

        if self.already_downloaded > 0:
            print(f"Already in archive      : {self.already_downloaded}")

        failed = self.total - self.successful - self.already_downloaded
        if failed > 0:
            print(f"Failed/Unavailable      : {failed}")

        attempted = self.total - self.already_downloaded
        if attempted > 0:
            success_rate = (self.successful / attempted) * 100
            print(f"\nSuccess rate: {success_rate:.1f}% ({self.successful}/{attempted})")

        print("=" * 70)


def download_playlist(url, use_archive=True, format_choice='1'):
    """Download all videos from a playlist"""
    downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")

    format_opts = get_format_options(format_choice)
    archive_file = os.path.join(downloads_dir, "yt_download_archive.txt")
    stats = PlaylistStats()

    ydl_opts = {
        'outtmpl': os.path.join(downloads_dir, '%(playlist)s/%(playlist_index)s - %(title)s.%(ext)s'),
        'noplaylist': False,  # Enable playlist download
        'ignoreerrors': True,  # Continue on errors
        'progress_hooks': [progress_hook, stats],
        'logger': stats,
        'quiet': False,
        'no_warnings': False,
        'socket_timeout': 30,  # Prevent hanging on slow connections
    }

    ydl_opts['format'] = format_opts['format']
    if 'postprocessors' in format_opts:
        ydl_opts['postprocessors'] = format_opts['postprocessors']

    if use_archive:
        ydl_opts['download_archive'] = archive_file
        print(f"Archive mode enabled. Tracking downloads in: {archive_file}")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print("\nExtracting playlist information...")
            info = ydl.extract_info(url, download=False)

            if info:
                playlist_title = info.get('title', 'Unknown Playlist')
                entries = info.get('entries', [])
                stats.total = len(entries)

                print(f"\nPlaylist : {playlist_title}")
                print(f"Total videos : {stats.total}")
                print(f"Format : {format_opts['format_name']}")
                print("-" * 50)

                items_to_download = stats.total - stats.already_downloaded
                if items_to_download == 0:
                    print("\nAll items already downloaded!")
                    return

                confirm = input(f"\nDownload {items_to_download} new items? (y/n): ").strip().lower()
                if confirm != 'y':
                    print("Download cancelled.")
                    return

                print(f"\nStarting downloads as {format_opts['format_name']}...")
                print("=" * 70)
                ydl.download([url])

                playlist_path = os.path.join(downloads_dir, playlist_title)
                stats.print_summary(playlist_title, playlist_path)

    except Exception as e:
        print(f"\nError downloading playlist: {e}")


def download_video(url, use_archive=True, format_choice='1', enable_duplicate_check=True):
    """Download a single video"""
    downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
    output_template = os.path.join(downloads_dir, "%(title)s.%(ext)s")

    format_opts = get_format_options(format_choice)
    archive_file = os.path.join(downloads_dir, "yt_download_archive.txt")

    hash_db_path = os.path.join(downloads_dir, "yt_hash_database.json")
    hash_db = load_hash_database(hash_db_path) if enable_duplicate_check else {}

    ydl_opts = {
        'format': format_opts['format'],
        'outtmpl': output_template,
        'noplaylist': True,
        'progress_hooks': [progress_hook],
        'socket_timeout': 30,  # Prevent hanging on slow connections
    }

    if 'postprocessors' in format_opts:
        ydl_opts['postprocessors'] = format_opts['postprocessors']

    if use_archive:
        ydl_opts['download_archive'] = archive_file
        print(f"Archive mode enabled. Tracking downloads in: {archive_file}")

    if enable_duplicate_check:
        print(f"Duplicate detection enabled. Hash database: {hash_db_path}")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"\nDownloading as {format_opts['format_name']}...")
            info = ydl.extract_info(url, download=True)

            if info:
                video_title = info.get('title', 'Unknown')
                print(f"\nDownload successful: {video_title}")
                print(f"Format: {format_opts['format_name']}")

                if enable_duplicate_check:
                    ext = info.get('ext', 'mp4')

                    if 'postprocessors' in ydl_opts:
                        for pp in ydl_opts['postprocessors']:
                            if pp.get('key') == 'FFmpegExtractAudio':
                                ext = pp.get('preferredcodec', ext)

                    possible_filenames = [
                        f"{video_title}.{ext}",
                        f"{sanitize_filename(video_title)}.{ext}"
                    ]

                    downloaded_file = None
                    for filename in possible_filenames:
                        filepath = os.path.join(downloads_dir, filename)
                        if os.path.exists(filepath):
                            downloaded_file = filepath
                            break

                    if not downloaded_file:
                        try:
                            recent_files = []
                            for file in os.listdir(downloads_dir):
                                if file.endswith(f".{ext}"):
                                    filepath = os.path.join(downloads_dir, file)
                                    if os.path.isfile(filepath):
                                        recent_files.append((filepath, os.path.getctime(filepath)))

                            if recent_files:
                                recent_files.sort(key=lambda x: x[1], reverse=True)
                                downloaded_file = recent_files[0][0]
                        except Exception as e:
                            print(f"Warning: Could not search for downloaded file: {e}")

                    if downloaded_file and os.path.exists(downloaded_file):
                        print(f"\nChecking for duplicates...")
                        file_hash = calculate_file_hash(downloaded_file)

                        if file_hash:
                            duplicate = check_duplicate(file_hash, hash_db)

                            if duplicate and duplicate['path'] != downloaded_file:
                                print(f"\nDUPLICATE DETECTED!")
                                print(f"This file is identical to:")
                                print(f"  {duplicate['path']}")
                                print(f"  {duplicate['title']}")
                                print(f"  Size: {format_bytes(duplicate['size'])}")

                                action = input(
                                    f"\nDelete duplicate file '{os.path.basename(downloaded_file)}'? (y/n): ").strip().lower()
                                if action == 'y':
                                    try:
                                        os.remove(downloaded_file)
                                        print(f"Duplicate file deleted.")
                                    except Exception as e:
                                        print(f"Could not delete file: {e}")
                                else:
                                    print(f"Keeping both files.")
                                    add_to_hash_database(downloaded_file, file_hash, hash_db, hash_db_path, video_title)
                            else:
                                add_to_hash_database(downloaded_file, file_hash, hash_db, hash_db_path, video_title)
                                print(f"File fingerprint saved to database.")
                    else:
                        print(f"Warning: Could not find downloaded file for duplicate check.")

    except yt_dlp.utils.DownloadError as e:
        if "has already been recorded in the archive" in str(e):
            print(f"\nVideo already downloaded (found in archive), skipping...")
        else:
            print(f"\nError: {e}")
    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    print("YouTube Downloader X - Video & Audio Downloader")
    print("=" * 60)

    link = input("Enter YouTube URL (video or playlist): ").strip()

    if link:
        use_archive_input = input("Enable archive mode to skip duplicates? (y/n): ").strip().lower()
        use_archive = use_archive_input != 'n'

        duplicate_check_input = input("Enable duplicate detection (compare file hashes)? (y/n): ").strip().lower()
        enable_duplicate_check = duplicate_check_input != 'n'

        format_choice = get_format_choice()

        print("\nAnalyzing URL...")

        if 'watch?' in link and 'list=' in link:
            playlist_choice = ask_playlist_or_video(link)

            if playlist_choice == '2':
                print("Downloading entire playlist!")
                download_playlist(link, use_archive, format_choice)
            else:
                print("Downloading single video!")
                download_video(link, use_archive, format_choice, enable_duplicate_check)

        elif is_playlist(link):
            print("Playlist detected!")
            download_playlist(link, use_archive, format_choice)
        else:
            print("Single video detected!")
            download_video(link, use_archive, format_choice, enable_duplicate_check)
    else:
        print("No URL provided.")