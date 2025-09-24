import socketio
import sounddevice as sd
import numpy as np
import uuid
import time
import threading

# تنظیمات بهینه برای حداقل تأخیر
sio = socketio.Client(reconnection_attempts=5, reconnection_delay=1)

# تنظیمات صدا
SAMPLE_RATE = 16000  # کاهش نرخ نمونه‌برداری
CHANNELS = 1
BUFFER_SIZE = 256    # بافر کوچک برای تأخیر کمتر
AUDIO_FORMAT = 'int16'
VOLUME = 0.8         # سطح صدا

sender_id = str(uuid.uuid4())
is_connected = False
stream_active = False

def audio_callback(indata, frames, time_info, status):
    global stream_active
    if not stream_active or not is_connected:
        return
    
    # پردازش و فشرده‌سازی صدا
    audio_data = (indata * VOLUME).astype(AUDIO_FORMAT)
    chunk = audio_data.tobytes()
    
    try:
        sio.emit("audio_chunk", {
            "chunk": chunk,
            "sender_id": sender_id
        })
    except:
        pass

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

@sio.event
def connect():
    global is_connected
    is_connected = True
    print("✓ متصل به سرور")
    sio.emit("register_sender", {"sender_id": sender_id})

@sio.event
def disconnect():
    global is_connected
    is_connected = False
    print("✗ قطع ارتباط با سرور")

@sio.on("connection_ack")
def handle_ack(data):
    print(f"شناسه اتصال شما: {data['sid']}")

def main():
    try:
        sio.connect("http://145.223.68.97:5000", transports=['websocket'])
        start_stream()
    except KeyboardInterrupt:
        print("\nقطع ارتباط...")
    except Exception as e:
        print(f"خطا: {str(e)}")
    finally:
        sio.disconnect()

if __name__ == "__main__":
    main()