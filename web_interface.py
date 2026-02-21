from flask import Flask, render_template, request, jsonify
import os
import json
import threading
from datetime import datetime
import main

app = Flask(__name__)

active_downloads = {}
download_history = []  # sqlite would be overkill for this, in-memory is fine for now


def make_progress_hook(download_id, is_playlist=False, total_videos=1):
    current_video = [0]
    video_title = [""]

    def hook(d):
        if active_downloads.get(download_id, {}).get('cancelled'):
            raise Exception('CANCELLED')

        if d['status'] == 'downloading':
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            speed = d.get('speed', 0)
            eta = d.get('eta', 0)

            # yt-dlp doesn't give us a clean "new video started" event,
            # so track title changes as a proxy for video switches
            info = d.get('info_dict', {})
            if info.get('title') and info['title'] != video_title[0]:
                video_title[0] = info['title']
                current_video[0] += 1

            if is_playlist and total_videos > 0:
                vid_pct = (downloaded / total * 100) if total > 0 else 0
                overall = ((current_video[0] - 1) / total_videos * 100) + (vid_pct / total_videos)
            else:
                overall = (downloaded / total * 100) if total > 0 else 0

            active_downloads[download_id].update({
                'status': 'downloading',
                'percent': overall,
                'downloaded': main.format_bytes(downloaded),
                'total': main.format_bytes(total) if total else '?',
                'speed': main.format_speed(speed),
                'eta': f"{eta}s" if eta else "?",
                'current_video': current_video[0],
                'total_videos': total_videos,
                'video_title': video_title[0]
            })

        elif d['status'] == 'finished':
            active_downloads[download_id].update({
                'status': 'downloading' if is_playlist else 'finished',
                'current_video': current_video[0],
            })

    return hook


def download_worker(url, format_choice, use_archive, enable_dup_check, download_id, is_playlist=False):
    try:
        downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        format_opts = main.get_format_options(format_choice)
        archive_file = os.path.join(downloads_dir, "yt_download_archive.txt")

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

        total_videos = 1
        playlist_title = "Unknown"

        if is_playlist:
            info_opts = {'quiet': True, 'no_warnings': True, 'extract_flat': True, 'socket_timeout': 30}
            with yt_dlp.YoutubeDL(info_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if info:
                    entries = [e for e in info.get('entries', []) if e]
                    total_videos = len(entries)
                    playlist_title = info.get('title', 'Unknown')

            active_downloads[download_id].update({
                'total_videos': total_videos,
                'title': playlist_title
            })

            print(f"Playlist: {playlist_title}, {total_videos} videos")

        hook = make_progress_hook(download_id, is_playlist, total_videos)

        ydl_opts = {
            'format': format_opts['format'],
            'outtmpl': os.path.join(downloads_dir, '%(title)s.%(ext)s'),
            'ignoreerrors': True,
            'quiet': True,
            'socket_timeout': 30,
            'progress_hooks': [hook]
        }

        if 'postprocessors' in format_opts:
            ydl_opts['postprocessors'] = format_opts['postprocessors']

        if use_archive:
            ydl_opts['download_archive'] = archive_file

        # hashing a full playlist would take forever and isn't worth it
        if enable_dup_check and not is_playlist:
            ydl_opts['_enable_dup_check'] = True

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

                cancelled = active_downloads[download_id].get('cancelled')
                status = 'stopped' if cancelled else 'completed'

                active_downloads[download_id].update({
                    'status': status,
                    'percent': 100,
                    'title': title
                })

                download_history.append({
                    'id': download_id,
                    'title': title,
                    'url': url,
                    'fmt': format_choice,
                    'status': status,
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
            print(f"Download error ({download_id}): {e}")
            active_downloads[download_id] = {'status': 'error', 'error': str(e)}
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
        return jsonify({'error': 'No URL'}), 400

    try:
        has_video = 'watch?' in url and 'v=' in url
        has_playlist = 'list=' in url

        if not has_playlist:
            return jsonify({'is_playlist': False, 'has_video': has_video, 'count': 0})

        import yt_dlp
        opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': 'in_playlist',
            'socket_timeout': 60,
            'ignoreerrors': True,
        }

        with yt_dlp.YoutubeDL(opts) as ydl:
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
    fmt = data.get('fmt', '1')
    use_archive = data.get('arc', True)
    dup_check = data.get('dup', True)
    mode = data.get('mode', 'auto')

    if not url:
        return jsonify({'error': 'No URL'}), 400

    if mode == 'auto':
        is_pl = main.is_playlist(url)
    elif mode == 'playlist':
        is_pl = True
    else:
        is_pl = False

    dl_id = f"dl_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    t = threading.Thread(
        target=download_worker,
        args=(url, fmt, use_archive, dup_check, dl_id, is_pl)
    )
    t.daemon = True
    t.start()

    return jsonify({'download_id': dl_id, 'status': 'started', 'is_playlist': is_pl})


@app.route('/stop/<download_id>', methods=['POST'])
def stop_download(download_id):
    if download_id in active_downloads:
        active_downloads[download_id]['cancelled'] = True
        active_downloads[download_id]['status'] = 'stopping'
        return jsonify({'status': 'stopping'})
    return jsonify({'error': 'Not found'}), 404


@app.route('/progress/<download_id>')
def get_progress(download_id):
    if download_id in active_downloads:
        return jsonify(active_downloads[download_id])
    return jsonify({'error': 'Not found'}), 404


@app.route('/history')
def get_history():
    return jsonify(download_history)


@app.route('/active')
def get_active():
    return jsonify(active_downloads)


if __name__ == '__main__':
    print("Starting on http://localhost:5001 (CTRL+C to stop)")
    app.run(host='0.0.0.0', port=5001, debug=True, threaded=True)