import socketio
import sounddevice as sd
import numpy as np
import queue
import threading

sio = socketio.Client()

SAMPLE_RATE = 44100
CHANNELS = 1
FRAMES_PER_BUFFER = 1024

audio_queue = queue.Queue()

def audio_playback():
    def callback(outdata, frames, time, status):
        try:
            data = audio_queue.get_nowait()
        except queue.Empty:
            outdata.fill(0)  # اگر صدایی نداشتیم سکوت بفرست
            return
        outdata[:] = data

    with sd.OutputStream(samplerate=SAMPLE_RATE, channels=CHANNELS,
                         dtype='int16', blocksize=FRAMES_PER_BUFFER,
                         callback=callback):
        print("🔊 Playing audio... (Ctrl+C to stop)")
        threading.Event().wait()

@sio.event
def connect():
    print("Connected to server")
    sio.emit("register_receiver")

@sio.event
def disconnect():
    print("Disconnected from server")

@sio.on("audio")
def on_audio(data):
    # تبدیل داده‌های بایت به numpy int16
    audio_chunk = np.frombuffer(data, dtype='int16')
    audio_chunk = audio_chunk.reshape(-1, CHANNELS)
    audio_queue.put(audio_chunk)

def main():
    sio.connect("https://h-musec.onrender.com")
    audio_playback()
    sio.wait()

if __name__ == "__main__":
    main()
