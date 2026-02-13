import yt_dlp
import os


def download_video(url):
    # Cross-platform way to target the user's Downloads folder
    downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads")
    output_template = os.path.join(downloads_dir, "%(title)s.%(ext)s")

    ydl_opts = {
        # Select best video with height <= 2160 (4K) + best audio
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': output_template,
        'noplaylist': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Download file to Downloads folder
            ydl.download([url])
        print("\nDownload successful!")
    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    link = input("Enter YouTube URL: ").strip()
    if link:
        download_video(link)