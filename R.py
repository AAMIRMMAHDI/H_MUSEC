import socket
import sounddevice as sd
import numpy as np
import threading
import time
from collections import deque

# تنظیمات صدا
SAMPLE_RATE = 16000
CHANNELS = 1
BUFFER_SIZE = 256
AUDIO_FORMAT = 'int16'
MAX_BUFFER_DURATION = 0.2  # حداکثر 200ms بافر برای جبران تأخیر شبکه

audio_buffer = deque(maxlen=int(SAMPLE_RATE * MAX_BUFFER_DURATION / BUFFER_SIZE))
is_playing = False
last_chunk_time = 0

TCP_HOST = "145.223.68.97"
TCP_PORT = 5000

def audio_callback(outdata, frames, time_info, status):
    global is_playing, last_chunk_time
    if not is_playing or len(audio_buffer) == 0:
        outdata.fill(0)
        return
    try:
        chunk = audio_buffer.popleft()
        outdata[:] = chunk
        last_chunk_time = time.time()
    except:
        outdata.fill(0)

def playback_thread():
    global is_playing
    is_playing = True
    with sd.OutputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype=AUDIO_FORMAT,
        blocksize=BUFFER_SIZE,
        callback=audio_callback
    ):
        print("🔊 شروع پخش صدا با تأخیر کم... (Ctrl+C برای توقف)")
        while is_playing:
            sd.sleep(100)

def tcp_listener():
    """اتصال TCP و دریافت داده‌ها"""
    global is_playing
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((TCP_HOST, TCP_PORT))
        print(f"✓ متصل به سرور TCP: {TCP_HOST}:{TCP_PORT}")

        while is_playing:
            data = sock.recv(4096)
            if not data:
                break
            try:
                chunk = np.frombuffer(data, dtype=AUDIO_FORMAT)
                chunk = chunk.reshape(-1, CHANNELS)
                audio_buffer.append(chunk)
            except:
                pass
    except Exception as e:
        print(f"✗ خطا در ارتباط TCP: {e}")
    finally:
        sock.close()
        print("✗ ارتباط TCP بسته شد")

def main():
    try:
        # شروع پخش صدا
        play_thread = threading.Thread(target=playback_thread, daemon=True)
        play_thread.start()

        # شروع دریافت از TCP
        tcp_thread = threading.Thread(target=tcp_listener, daemon=True)
        tcp_thread.start()

        play_thread.join()
    except KeyboardInterrupt:
        print("\nقطع ارتباط...")
    finally:
        global is_playing
        is_playing = False

if __name__ == "__main__":
    main()
