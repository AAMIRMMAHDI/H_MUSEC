import socket
import json
import struct
import sounddevice as sd
import numpy as np
import time
import threading
from collections import deque

# تنظیمات (مثل قبل)
HOST = '127.0.0.1'
PORT = 5000
SAMPLE_RATE = 16000
CHANNELS = 1
BUFFER_SIZE = 256
AUDIO_FORMAT = np.int16
MAX_BUFFER_DURATION = 0.32  # بزرگ‌تر: 320ms برای جلوگیری از underrun/crackling

audio_buffer = deque(maxlen=int(SAMPLE_RATE * MAX_BUFFER_DURATION / BUFFER_SIZE) * 2)  # دو برابر برای ایمنی
is_playing = False
last_chunk_time = 0
is_connected = False
client_socket = None

def audio_callback(outdata, frames, time_info, status):
    global is_playing, last_chunk_time
    if status:  # اگر underrun، silence
        print("Underrun detected!")
        outdata.fill(0)
        return

    if not is_playing or len(audio_buffer) == 0:
        outdata.fill(0)
        return

    try:
        chunk = audio_buffer.popleft()
        outdata[:] = chunk
        last_chunk_time = time.time()
        # اگر buffer خیلی خالی شد، warning
        if len(audio_buffer) < 5:
            print("Buffer low - potential crackling!")
    except Exception as e:
        print(f"Callback error: {e}")
        outdata.fill(0)

def playback_thread():
    global is_playing
    is_playing = True

    with sd.OutputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype=AUDIO_FORMAT,
        blocksize=BUFFER_SIZE,
        callback=audio_callback,
        latency='low'  # low latency، اما با buffer بزرگ جبران می‌شه
    ):
        print("🔊 شروع پخش...")
        while is_playing:
            sd.sleep(10)  # کوچکتر

def receive_messages():
    global is_connected, client_socket, is_playing
    while is_connected:
        try:
            length_data = client_socket.recv(4)
            if len(length_data) < 4:
                break
            length = struct.unpack('!I', length_data)[0]
            data = b''
            while len(data) < length:
                packet = client_socket.recv(length - len(data))
                if not packet:
                    break
                data += packet
            if not data:
                break

            # parse: JSON | chunk
            parts = data.split(b'|', 1)
            if len(parts) != 2:
                continue
            json_part = parts[0].decode('utf-8')
            chunk_bytes = parts[1]

            message = json.loads(json_part)
            handle_message(message, chunk_bytes)
        except Exception as e:
            print(f"خطا در دریافت: {e}")
            break
    is_connected = False
    is_playing = False
    print("✗ قطع")

def handle_message(message, chunk_bytes):
    action = message.get("action")
    if action == "connection_ack":
        print(f"شناسه: {message['sid']}")
    elif action == "audio_stream":
        try:
            chunk = np.frombuffer(chunk_bytes, dtype=AUDIO_FORMAT)
            chunk = chunk.reshape(-1, CHANNELS)
            audio_buffer.append(chunk)
        except Exception as e:
            print(f"خطا در chunk: {e}")
    elif action == "user_update":
        print(f"آپدیت: {message['ar']} فرستنده، {message['vr']} گیرنده")

def main():
    global client_socket, is_connected, is_playing
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((HOST, PORT))
        is_connected = True
        print("✓ متصل")

        # register
        reg_msg = json.dumps({"action": "register_receiver"}).encode('utf-8')
        header = struct.pack('!I', len(reg_msg))
        client_socket.send(header + reg_msg)

        threading.Thread(target=receive_messages, daemon=True).start()
        playback_thread()

    except KeyboardInterrupt:
        print("\nقطع...")
    except Exception as e:
        print(f"خطا: {e}")
    finally:
        is_playing = False
        is_connected = False
        if client_socket:
            client_socket.close()

if __name__ == "__main__":
    main()