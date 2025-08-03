import socketio
import sounddevice as sd
import numpy as np
import uuid
import time
import threading

# تنظیمات صدا
SAMPLE_RATE = 16000
CHANNELS = 1
BUFFER_SIZE = 256
AUDIO_FORMAT = 'int16'
VOLUME = 1.5  # سطح صدا

sio = socketio.Client(reconnection_attempts=5, reconnection_delay=1)

sender_id = str(uuid.uuid4())
is_connected = False
stream_active = False

def audio_callback(indata, frames, time_info, status):
    global stream_active
    if not stream_active or not is_connected:
        return
    
    try:
        audio_data = (indata * VOLUME).clip(-0.99, 0.99)
        chunk = audio_data.astype(AUDIO_FORMAT).tobytes()
        
        sio.emit("audio_chunk", {
            "chunk": chunk,
            "sender_id": sender_id,
            "timestamp": time.time()
        })
    except Exception as e:
        print(f"Audio error: {str(e)}")

def start_stream():
    global stream_active
    
    input_device = None
    try:
        input_devices = [d for d in sd.query_devices() if d['max_input_channels'] > 0]
        input_device = input_devices[0]['index'] if input_devices else None
    except:
        pass

    stream_active = True
    print("🎤 شروع ارسال صدا... (Ctrl+C برای توقف)")
    print(f"شناسه فرستنده: {sender_id}")
    print(f"تنظیمات: نرخ نمونه‌برداری={SAMPLE_RATE}Hz, حجم صدا={VOLUME}x")
    
    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype='float32',
        blocksize=BUFFER_SIZE,
        callback=audio_callback,
        device=input_device
    ):
        while stream_active:
            sd.sleep(100)

@sio.event
def connect():
    global is_connected
    is_connected = True
    print("✓ متصل به سرور آنلاین")
    sio.emit("register_sender", {"sender_id": sender_id})

@sio.event
def disconnect():
    global is_connected
    is_connected = False
    print("✗ قطع ارتباط با سرور")

@sio.on("connection_ack")
def handle_ack(data):
    if 'config' in data:
        print(f"تنظیمات سرور: نرخ نمونه‌برداری {data['config']['sample_rate']}Hz")

def main():
    try:
        print("در حال اتصال به سرور آنلاین...")
        sio.connect("https://h-musec.onrender.com", transports=['websocket'])
        start_stream()
    except KeyboardInterrupt:
        print("\nقطع ارتباط...")
    except Exception as e:
        print(f"خطا: {str(e)}")
        print("مطمئن شوید سرور آنلاین فعال است و اینترنت متصل است")
    finally:
        sio.disconnect()

if __name__ == "__main__":
    main()