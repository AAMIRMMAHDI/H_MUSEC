import socketio
import sounddevice as sd
import numpy as np

sio = socketio.Client()
SAMPLERATE = 44100
CHUNK = 1024

def play_audio(data):
    audio = np.frombuffer(data, dtype='int16')
    sd.play(audio, samplerate=SAMPLERATE, blocking=False)

@sio.on('audio')
def on_audio(data):
    play_audio(data)

sio.connect('https://h-musec.onrender.com')
print("🔊 Listening for audio...")
sio.wait()
