import socketio
import sounddevice as sd
import threading

sio = socketio.Client()

SAMPLE_RATE = 44100
CHANNELS = 1
FRAMES_PER_BUFFER = 1024  # اندازه بلوک صوتی
connected = False

def audio_callback(indata, frames, time, status):
    if status:
        print(f"Status: {status}")
    if connected:
        # ارسال داده‌ها به صورت بایت
        sio.emit("audio", indata.tobytes())

def start_audio_stream():
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS,
                        dtype='int16', blocksize=FRAMES_PER_BUFFER,
                        callback=audio_callback):
        print("🎤 Sending audio... (Ctrl+C to stop)")
        threading.Event().wait()  # حفظ اجرای برنامه تا Ctrl+C

@sio.event
def connect():
    global connected
    connected = True
    print("Connected to server")
    sio.emit("register_sender")

@sio.event
def disconnect():
    global connected
    connected = False
    print("Disconnected from server")

def main():
    sio.connect("https://h-musec.onrender.com")
    start_audio_stream()
    sio.wait()

if __name__ == "__main__":
    main()
