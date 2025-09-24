import socket
import json
import struct  # برای length header
import sounddevice as sd
import numpy as np
import uuid
import time
import threading

# تنظیمات (مثل قبل)
HOST = '127.0.0.1'
PORT = 5000
SAMPLE_RATE = 16000
CHANNELS = 1
BUFFER_SIZE = 256  # کوچک نگه دار برای low latency
AUDIO_FORMAT = np.int16  # تغییر به np.int16 برای سازگاری
VOLUME = 0.8

sender_id = str(uuid.uuid4())
is_connected = False
stream_active = False
client_socket = None

def audio_callback(indata, frames, time_info, status):
    global stream_active, is_connected, client_socket
    if not stream_active or not is_connected or status:
        return (indata * 0).astype(AUDIO_FORMAT)  # silence اگر مشکلی باشه

    audio_data = (indata * VOLUME).astype(AUDIO_FORMAT)
    chunk_bytes = audio_data.tobytes()

    try:
        message = json.dumps({
            "action": "audio_chunk",
            "sender_id": sender_id
        }).encode('utf-8')
        full_data = message + b'|' + chunk_bytes  # separator
        header = struct.pack('!I', len(full_data))  # length header
        client_socket.send(header + full_data)
    except Exception as e:
        print(f"خطا در ارسال: {e}")

def start_stream():
    global stream_active
    stream_active = True
    print("🎤 شروع ارسال...")

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype=AUDIO_FORMAT,
        blocksize=BUFFER_SIZE,  # explicit نگه دار، اما کوچک
        callback=audio_callback,
        latency='low'  # low latency
    ):
        while stream_active:
            sd.sleep(10)  # کوچکتر برای responsiveness

def receive_messages():
    global is_connected, client_socket
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

            try:
                message = json.loads(data.decode('utf-8'))
                handle_message(message)
            except json.JSONDecodeError:
                print(f"پیام نامعتبر: {data}")
        except Exception as e:
            print(f"خطا در دریافت: {e}")
            break
    is_connected = False

def handle_message(message):
    action = message.get("action")
    if action == "connection_ack":
        print(f"شناسه: {message['sid']}")
    elif action == "user_update":
        print(f"آپدیت: {message['ar']} فرستنده، {message['vr']} گیرنده")

def main():
    global client_socket, is_connected, stream_active
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((HOST, PORT))
        is_connected = True
        print("✓ متصل")

        # register
        reg_msg = json.dumps({"action": "register_sender", "sender_id": sender_id}).encode('utf-8')
        header = struct.pack('!I', len(reg_msg))
        client_socket.send(header + reg_msg)

        threading.Thread(target=receive_messages, daemon=True).start()
        start_stream()

    except KeyboardInterrupt:
        print("\nقطع...")
    except Exception as e:
        print(f"خطا: {e}")
    finally:
        stream_active = False
        is_connected = False
        if client_socket:
            client_socket.close()

if __name__ == "__main__":
    main()