from flask import Flask
from flask_socketio import SocketIO, emit
import eventlet

eventlet.monkey_patch()

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def index():
    return '🔊 Audio relay server is running!'

@socketio.on('audio')
def handle_audio(data):
    emit('audio', data, broadcast=True, include_self=False)

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=5000)
