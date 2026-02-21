from flask import Flask, render_template, request, jsonify, Response
import os
import json
import threading
from datetime import datetime
from queue import Queue
import main

app = Flask(__name__)

active_downloads = {}
download_queue = Queue()
download_history = []


class WebProgressHook:
    """Progress hook with cancellation support"""

    def __init__(self, download_id, is_playlist=False, total_videos=1):
        self.download_id = download_id
        self.is_playlist = is_playlist
        self.total_videos = total_videos
        self.current_video = 0
        self.video_title = ""

    def __call__(self, d):
        # Check for cancellation
        if active_downloads.get(self.download_id, {}).get('cancelled'):
            raise Exception('CANCELLED')

        # Track playlist video changes
        if d['status'] == 'started':
            self.current_video += 1
            self.video_title = d.get('info_dict', {}).get('title', 'Unknown')

        if d['status'] == 'downloading':
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            speed = d.get('speed', 0)
            eta = d.get('eta', 0)

            # Calculate overall playlist progress
            if self.is_playlist and self.total_videos > 0:
                video_progress = (downloaded / total * 100) if total > 0 else 0
                overall_percent = ((self.current_video - 1) / self.total_videos * 100) + (
                            video_progress / self.total_videos)
            else:
                overall_percent = (downloaded / total * 100) if total > 0 else 0

            active_downloads[self.download_id].update({
                'status': 'downloading_playlist' if self.is_playlist else 'downloading',
                'percent': overall_percent,
                'downloaded': main.format_bytes(downloaded),
                'total': main.format_bytes(total),
                'speed': main.format_speed(speed),
                'eta': f"{eta}s" if eta else "Unknown",
                'current_video': self.current_video,
                'total_videos': self.total_videos,
                'video_title': self.video_title
            })

        elif d['status'] == 'finished':
            active_downloads[self.download_id].update({
                'status': 'downloading_playlist' if self.is_playlist else 'finished',
                'current_video': self.current_video,
                'total_videos': self.total_videos
            })


def download_worker(url, format_choice, use_archive, enable_duplicate_check, download_id, is_playlist=False):
    """Background download worker"""
    try:
        downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        format_opts = main.get_format_options(format_choice)
        archive_file = os.path.join(downloads_dir, "yt_download_archive.txt")

        # Init active download
        active_downloads[download_id] = {
            'status': 'starting',
            'percent': 0,
            'cancelled': False,
            'url': url,
            'is_playlist': is_playlist,
            'current_video': 0,
            'total_videos': 0
        }

        import yt_dlp

        # First extract info to get playlist count
        info_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'socket_timeout': 30,
        }

        total_videos = 1
        playlist_title = "Unknown"

        if is_playlist:
            with yt_dlp.YoutubeDL(info_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if info:
                    entries = [e for e in info.get('entries', []) if e]
                    total_videos = len(entries)
                    playlist_title = info.get('title', 'Unknown Playlist')

            active_downloads[download_id].update({
                'total_videos': total_videos,
                'title': playlist_title
            })

        # Setup download options
        ydl_opts = {
            'format': format_opts['format'],
            'outtmpl': os.path.join(downloads_dir, '%(title)s.%(ext)s'),
            'ignoreerrors': True,
            'quiet': True,
            'socket_timeout': 30,
            'progress_hooks': [WebProgressHook(download_id, is_playlist, total_videos)]
        }

        if 'postprocessors' in format_opts:
            ydl_opts['postprocessors'] = format_opts['postprocessors']

        if use_archive:
            ydl_opts['download_archive'] = archive_file

        if is_playlist:
            ydl_opts['noplaylist'] = False
            ydl_opts['outtmpl'] = os.path.join(downloads_dir, '%(playlist)s/%(playlist_index)s - %(title)s.%(ext)s')
        else:
            ydl_opts['noplaylist'] = True

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

            if info:
                title = info.get('title', 'Unknown')
                if is_playlist:
                    entries = [e for e in info.get('entries', []) if e]
                    title = f"{playlist_title} ({len(entries)} videos)"

                # Check if cancelled
                if active_downloads[download_id].get('cancelled'):
                    active_downloads[download_id]['status'] = 'stopped'
                else:
                    active_downloads[download_id].update({
                        'status': 'completed',
                        'percent': 100,
                        'title': title
                    })

                download_history.append({
                    'id': download_id,
                    'title': title,
                    'url': url,
                    'fmt': format_choice,
                    'status': 'completed' if not active_downloads[download_id].get('cancelled') else 'stopped',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })

    except Exception as e:
        if 'CANCELLED' in str(e):
            active_downloads[download_id]['status'] = 'stopped'
            download_history.append({
                'id': download_id,
                'url': url,
                'status': 'stopped',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        else:
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
    return render_template('index.html')


@app.route('/playlist_info', methods=['POST'])
def playlist_info():
    data = request.json
    url = data.get('url')

    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    try:
        has_video = 'watch?' in url and 'v=' in url
        has_playlist = 'list=' in url

        if not has_playlist:
            return jsonify({'is_playlist': False, 'has_video': has_video, 'count': 0})

        import yt_dlp
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': 'in_playlist',
            'socket_timeout': 60,
            'ignoreerrors': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            if info and info.get('_type') == 'playlist':
                entries = [e for e in info.get('entries', []) if e]
                return jsonify({
                    'is_playlist': True,
                    'has_video': has_video,
                    'title': info.get('title', 'Unknown'),
                    'count': len(entries)
                })

        return jsonify({'is_playlist': False, 'has_video': has_video, 'count': 0})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/download', methods=['POST'])
def start_download():
    data = request.json
    url = data.get('url')
    format_choice = data.get('fmt', '1')
    use_archive = data.get('arc', True)
    enable_duplicate_check = data.get('dup', True)
    download_mode = data.get('mode', 'auto')

    if not url:
        return jsonify({'error': 'No URL provided'}), 400

    is_pl = main.is_playlist(url) if download_mode == 'auto' else (download_mode == 'playlist')
    if download_mode == 'video':
        is_pl = False

    download_id = f"dl_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    thread = threading.Thread(
        target=download_worker,
        args=(url, format_choice, use_archive, enable_duplicate_check, download_id, is_pl)
    )
    thread.daemon = True
    thread.start()

    return jsonify({
        'download_id': download_id,
        'status': 'started',
        'is_playlist': is_pl
    })


@app.route('/stop/<download_id>', methods=['POST'])
def stop_download(download_id):
    """Stop active download"""
    if download_id in active_downloads:
        active_downloads[download_id]['cancelled'] = True
        active_downloads[download_id]['status'] = 'stopping'
        return jsonify({'message': 'Stopping download...', 'status': 'stopping'})
    return jsonify({'error': 'Download not found'}), 404


@app.route('/progress/<download_id>')
def get_progress(download_id):
    if download_id in active_downloads:
        return jsonify(active_downloads[download_id])
    return jsonify({'error': 'Download not found'}), 404


@app.route('/history')
def get_history():
    return jsonify(download_history)


@app.route('/active')
def get_active():
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
    app.run(host='0.0.0.0', port=5001, debug=True, threaded=True)