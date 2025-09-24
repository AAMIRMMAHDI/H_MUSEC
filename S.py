import socket
import sounddevice as sd
import numpy as np
import uuid
import threading

# تنظیمات صدا
SAMPLE_RATE = 16000
CHANNELS = 1
BUFFER_SIZE = 256
AUDIO_FORMAT = 'int16'
VOLUME = 0.8

# تنظیمات TCP
TCP_HOST = "145.223.68.97"
TCP_PORT = 5000

sender_id = str(uuid.uuid4())
stream_active = False
tcp_socket = None

def audio_callback(indata, frames, time_info, status):
    global tcp_socket, stream_active
    if not stream_active or tcp_socket is None:
        return

    audio_data = (indata * VOLUME).astype(AUDIO_FORMAT)
    chunk = audio_data.tobytes()

    try:
        # قبل از ارسال، طول داده رو هم می‌فرستیم تا سمت سرور بدونه چقدر بخونه
        length_prefix = len(chunk).to_bytes(4, byteorder='big')
        tcp_socket.sendall(length_prefix + chunk)
    except:
        stream_active = False
        print("✗ ارتباط TCP قطع شد")

def start_stream():
    global stream_active
    stream_active = True
    print("🎤 شروع ارسال صدا با تأخیر کم... (Ctrl+C برای توقف)")

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype=AUDIO_FORMAT,
        blocksize=BUFFER_SIZE,
        callback=audio_callback
    ):
        while stream_active:
            sd.sleep(100)

def main():
    global tcp_socket, stream_active
    try:
        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_socket.connect((TCP_HOST, TCP_PORT))
        print(f"✓ متصل به سرور TCP: {TCP_HOST}:{TCP_PORT}")

        start_stream()
    except KeyboardInterrupt:
        print("\nقطع ارتباط...")
    except Exception as e:
        print(f"✗ خطا: {e}")
    finally:
        stream_active = False
        if tcp_socket:
            tcp_socket.close()
            print("✗ ارتباط TCP بسته شد")

if __name__ == "__main__":
    main()
