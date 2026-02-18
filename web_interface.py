from flask import Flask, render_template, request, jsonify, Response
import os
import json
import threading
from datetime import datetime
from queue import Queue
import main  # Import functions from main.py

app = Flask(__name__)

# Store active downloads
active_downloads = {}
download_queue = Queue()
download_history = []


class WebProgressHook:
    """Custom progress hook for web interface"""

    def __init__(self, download_id):
        self.download_id = download_id
        self.progress_data = {
            'status': 'downloading',
            'percent': 0,
            'downloaded': 0,
            'total': 0,
            'speed': 0,
            'eta': 0
        }

    def __call__(self, d):
        if d['status'] == 'downloading':
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            speed = d.get('speed', 0)
            eta = d.get('eta', 0)

            self.progress_data.update({
                'status': 'downloading',
                'percent': (downloaded / total * 100) if total > 0 else 0,
                'downloaded': main.format_bytes(downloaded),
                'total': main.format_bytes(total),
                'speed': main.format_speed(speed),
                'eta': f"{eta}s" if eta else "Unknown"
            })

            active_downloads[self.download_id] = self.progress_data

        elif d['status'] == 'finished':
            self.progress_data.update({
                'status': 'finished',
                'percent': 100
            })
            active_downloads[self.download_id] = self.progress_data


def download_worker(url, format_choice, use_archive, enable_duplicate_check, download_id):
    """Background worker for downloads"""
    try:
        # Create custom progress hook
        progress_hook = WebProgressHook(download_id)

        # Modify download_video to use custom progress hook
        downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        output_template = os.path.join(downloads_dir, "%(title)s.%(ext)s")
        format_opts = main.get_format_options(format_choice)
        archive_file = os.path.join(downloads_dir, "yt_download_archive.txt")
        hash_db_path = os.path.join(downloads_dir, "yt_hash_database.json")
        hash_db = main.load_hash_database(hash_db_path) if enable_duplicate_check else {}

        ydl_opts = {
            'format': format_opts['format'],
            'outtmpl': output_template,
            'noplaylist': True,
            'progress_hooks': [progress_hook],
            'quiet': True
        }

        if 'postprocessors' in format_opts:
            ydl_opts['postprocessors'] = format_opts['postprocessors']

        if use_archive:
            ydl_opts['download_archive'] = archive_file

        import yt_dlp
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

            if info:
                video_title = info.get('title', 'Unknown')

                # Add to history
                download_history.append({
                    'id': download_id,
                    'title': video_title,
                    'url': url,
                    'format': format_opts['format_name'],
                    'status': 'completed',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })

                # Handle duplicate detection if enabled
                if enable_duplicate_check:
                    ext = info.get('ext', 'mp4')
                    if 'postprocessors' in ydl_opts:
                        for pp in ydl_opts['postprocessors']:
                            if pp.get('key') == 'FFmpegExtractAudio':
                                ext = pp.get('preferredcodec', ext)

                    expected_filename = f"{video_title}.{ext}"
                    downloaded_file = os.path.join(downloads_dir, expected_filename)

                    if os.path.exists(downloaded_file):
                        file_hash = main.calculate_file_hash(downloaded_file)
                        if file_hash:
                            duplicate = main.check_duplicate(file_hash, hash_db)
                            if not duplicate or duplicate['path'] == downloaded_file:
                                main.add_to_hash_database(downloaded_file, file_hash, hash_db, hash_db_path,
                                                          video_title)

                active_downloads[download_id]['status'] = 'completed'
                active_downloads[download_id]['title'] = video_title

    except Exception as e:
        active_downloads[download_id] = {
            'status': 'error',
            'error': str(e)
        }
        download_history.append({
            'id': download_id,
            'url': url,
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@app.route('/download', methods=['POST'])
def start_download():
    """Start a new download"""
    data = request.json
    url = data.get('url')
    format_choice = data.get('format', '1')
    use_archive = data.get('archive', True)
    enable_duplicate_check = data.get('duplicate_check', True)

    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    # Generate download ID
    download_id = f"dl_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Initialize progress
    active_downloads[download_id] = {
        'status': 'starting',
        'percent': 0,
        'url': url
    }

    # Start download in background thread
    thread = threading.Thread(
        target=download_worker,
        args=(url, format_choice, use_archive, enable_duplicate_check, download_id)
    )
    thread.daemon = True
    thread.start()

    return jsonify({'download_id': download_id, 'status': 'started'})


@app.route('/progress/<download_id>')
def get_progress(download_id):
    """Get progress of a specific download"""
    if download_id in active_downloads:
        return jsonify(active_downloads[download_id])
    return jsonify({'error': 'Download not found'}), 404


@app.route('/history')
def get_history():
    """Get download history"""
    return jsonify(download_history)


@app.route('/active')
def get_active():
    """Get all active downloads"""
    return jsonify(active_downloads)


if __name__ == '__main__':
    print("=" * 60)
    print("🌐 YouTube Downloader X - Web Interface")
    print("=" * 60)
    print("\n🚀 Starting web server...")
    print("📱 Access the interface at: http://localhost:5001")
    print("🌍 Or from another device: http://YOUR_IP:5001")
    print("\n⚠️  Press CTRL+C to stop the server\n")
    print("=" * 60)

    # Run Flask app on port 5001 to avoid conflict with macOS AirPlay
    app.run(host='0.0.0.0', port=5001, debug=True, threaded=True)