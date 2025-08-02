import sounddevice as sd
import socketio

sio = socketio.Client()
RATE = 44100
CHANNELS = 1
CHUNK = 1024

audio_buffer = bytearray()

@sio.event
def connect():
    print("Connected to server")
    sio.emit("register_receiver")

@sio.event
def disconnect():
    print("Disconnected from server")

@sio.on("audio")
def on_audio(data):
    # داده باینری را به آرایه numpy تبدیل می کنیم و پخش می کنیم
    audio = memoryview(data)
    # پخش صدا به صورت همزمان و سریع
    sd.play(audio, samplerate=RATE)

if __name__ == "__main__":
    sio.connect("https://h-musec.onrender.com")
    print("🎧 Receiving audio... (Ctrl+C to stop)")
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopped receiving audio.")
    finally:
        sio.disconnect()
