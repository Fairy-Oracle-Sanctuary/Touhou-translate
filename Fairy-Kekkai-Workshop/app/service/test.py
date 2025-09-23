import yt_dlp

ydl_opts = {
    'format': 'bv[ext=mp4]+ba[ext=m4a]',
    'embedmetadata': True,
    'merge_output_format': 'mp4',
    'outtmpl': r'D:\东方project\projects\test\1\生肉.%(ext)s',
}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    ydl.download(['https://www.youtube.com/watch?v=8JYAMS0Dar0&t=1s'])