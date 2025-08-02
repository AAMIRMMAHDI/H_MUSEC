import socketio
import sounddevice as sd
import numpy as np

sio = socketio.Client()
sio.connect('https://h-musec.onrender.com')

SAMPLERATE = 44100
CHUNK = 1024

def callback(indata, frames, time, status):
    if status:
        print(status)
    sio.emit('audio', indata.tobytes())

with sd.InputStream(samplerate=SAMPLERATE, channels=1, dtype='int16', callback=callback, blocksize=CHUNK):
    print("🎤 Sending audio...")
    sio.wait()
