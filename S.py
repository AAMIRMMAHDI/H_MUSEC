import sounddevice as sd
import socketio
import threading

sio = socketio.Client()
RATE = 44100
CHANNELS = 1
CHUNK = 1024

@sio.event
def connect():
    print("Connected to server")
    sio.emit("register_sender")

@sio.event
def disconnect():
    print("Disconnected from server")

def callback(indata, frames, time, status):
    if status:
        print(status)
    # ارسال داده صوتی به سرور (باینری)
    sio.emit("audio", indata.tobytes())

def start_stream():
    with sd.InputStream(samplerate=RATE, channels=CHANNELS, blocksize=CHUNK, callback=callback):
        print("🎤 Sending audio... (Ctrl+C to stop)")
        while True:
            sd.sleep(1000)

if __name__ == "__main__":
    sio.connect("https://h-musec.onrender.com")
    try:
        start_stream()
    except KeyboardInterrupt:
        print("Stopped sending audio.")
    finally:
        sio.disconnect()
