import yt_dlp
import os
import sys
import hashlib
import json


def format_bytes(b):
    if b < 1024:
        return f"{b:.2f} B"
    elif b < 1024 * 1024:
        return f"{b / 1024:.2f} KB"
    elif b < 1024 * 1024 * 1024:
        return f"{b / (1024 * 1024):.2f} MB"
    else:
        return f"{b / (1024 * 1024 * 1024):.2f} GB"


def format_speed(speed):
    if speed is None:
        return "Unknown"
    return f"{format_bytes(speed)}/s"


def calc_hash(file_path):
    h = hashlib.sha256()
    try:
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()
    except OSError as e:
        print(f"Warning: Could not hash {file_path}: {e}")
        return None


def load_hash_db(db_path):
    if os.path.exists(db_path):
        with open(db_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_hash_db(db_path, hash_db):
    try:
        with open(db_path, 'w', encoding='utf-8') as f:
            json.dump(hash_db, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"Warning: Could not save hash db: {e}")


def check_duplicate(file_hash, hash_db):
    if file_hash in hash_db:
        return hash_db[file_hash]
    return None


def add_to_hash_db(file_path, file_hash, hash_db, db_path, title=None):
    exists = os.path.exists(file_path)
    hash_db[file_hash] = {
        'path': file_path,
        'title': title or os.path.basename(file_path),
        'size': os.path.getsize(file_path) if exists else 0,
        'added': os.path.getctime(file_path) if exists else 0
    }
    save_hash_db(db_path, hash_db)


def sanitize_filename(filename):
    for char in '<>:"/\\|?*':
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
            filled = int(30 * downloaded // total)
        else:
            percent = 0
            filled = 0

        bar = '#' * filled + '-' * (30 - filled)
        speed_str = format_speed(speed) if speed else "?"
        eta_str = f"{eta}s" if eta else "?"
        total_str = format_bytes(total) if total > 0 else "?"

        sys.stdout.write(
            f'\r[{bar}] {percent:.1f}% | {format_bytes(downloaded)}/{total_str} | {speed_str} | ETA: {eta_str}   '
        )
        sys.stdout.flush()
    elif d['status'] == 'finished':
        downloaded = d.get('downloaded_bytes', 0)
        sys.stdout.write(f'\rDone: {format_bytes(downloaded)}' + ' ' * 50 + '\n')
        sys.stdout.flush()


def get_format_options(format_choice):
    if format_choice == '1':
        return {'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best', 'format_name': 'Video (MP4)'}
    elif format_choice == '2':
        return {'format': 'bestaudio/best',
                'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
                'format_name': 'Audio (MP3)'}
    elif format_choice == '3':
        return {'format': 'bestaudio[ext=m4a]/bestaudio/best',
                'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'm4a'}],
                'format_name': 'Audio (M4A)'}
    elif format_choice == '4':
        return {'format': 'bestaudio/best', 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'wav'}],
                'format_name': 'Audio (WAV)'}
    return {'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best', 'format_name': 'Video (MP4)'}


def is_playlist(url):
    if 'watch?' not in url and 'list=' in url:
        return True
    ydl_opts = {'quiet': True, 'no_warnings': True, 'extract_flat': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get('_type') == 'playlist'
    except:
        return False


def download_video(url, use_archive=True, format_choice='1', enable_duplicate_check=True):
    downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
    format_opts = get_format_options(format_choice)
    archive_file = os.path.join(downloads_dir, "yt_download_archive.txt")
    hash_db_path = os.path.join(downloads_dir, "yt_hash_database.json")
    hash_db = load_hash_db(hash_db_path) if enable_duplicate_check else {}

    ydl_opts = {
        'format': format_opts['format'],
        'outtmpl': os.path.join(downloads_dir, '%(title)s.%(ext)s'),
        'noplaylist': True,
        'progress_hooks': [progress_hook],
        'socket_timeout': 30,
    }
    if 'postprocessors' in format_opts:
        ydl_opts['postprocessors'] = format_opts['postprocessors']
    if use_archive:
        ydl_opts['download_archive'] = archive_file

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"\nDownloading as {format_opts['format_name']}...")
            info = ydl.extract_info(url, download=True)
            if not info: return

            video_title = info.get('title', 'Unknown')
            ext = info.get('ext', 'mp4')
            if 'postprocessors' in ydl_opts:
                for pp in ydl_opts['postprocessors']:
                    if pp.get('key') == 'FFmpegExtractAudio':
                        ext = pp.get('preferredcodec', ext)

            downloaded_file = os.path.join(downloads_dir, f"{sanitize_filename(video_title)}.{ext}")

            if os.path.exists(downloaded_file) and enable_duplicate_check:
                file_hash = calc_hash(downloaded_file)
                if file_hash:
                    duplicate = check_duplicate(file_hash, hash_db)
                    if not duplicate:
                        add_to_hash_db(downloaded_file, file_hash, hash_db, hash_db_path, video_title)
                        print("File hashed and saved.")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    print("--- YouTube Downloader CLI Core ---")
    link = input("URL: ").strip()
    if link:
        download_video(link, format_choice='1')