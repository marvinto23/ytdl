from flask import Flask, render_template, request, send_from_directory
from flask_socketio import SocketIO, emit
import yt_dlp
import os
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'bEanczuesrf'
socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('index.html', audio_only=True)

@app.route('/', methods=['POST'])
def download_video():
    def progress_hook(progress):
        if progress['status'] == 'downloading':
            percent = progress['_percent_str']
            socketio.emit('progress', {'percent': percent}, namespace='/download')

    url = request.form['url']
    format = request.form['format']
    audio_only = 'audio_only' in request.form

    ydl_opts = {
        'format': 'bestaudio/best' if audio_only else 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio',
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': format}] if audio_only else [],
        'outtmpl': f'downloads/%(title)s.%(ext)s',
        'progress_hooks': [progress_hook],
        'playlistend': 10, # limit to maximum 10 videos in playlist
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    filename = ydl.prepare_filename(ydl.extract_info(url, download=False))
    file_ext = format if audio_only else ydl_opts['format'].split('+')[-1].split('/')[0]
    filename = filename.replace('.webm', f'.{file_ext}').replace('.mp4', f'.{file_ext}')

    return send_from_directory('downloads', os.path.basename(filename), as_attachment=True)

@socketio.on('connect', namespace='/download')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect', namespace='/download')
def handle_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=80)
