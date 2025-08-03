import socketio
import sounddevice as sd
import numpy as np
import uuid
import time
import threading
import audioop

# تنظیمات پیشرفته صدا
SAMPLE_RATE = 16000
CHANNELS = 1
BUFFER_SIZE = 256
AUDIO_FORMAT = 'int16'
VOLUME = 1.8  # افزایش حجم صدا (1.0 = نرمال)
NOISE_REDUCTION = True  # فعال کردن کاهش نویز

sio = socketio.Client(reconnection_attempts=5, reconnection_delay=1)

sender_id = str(uuid.uuid4())
is_connected = False
stream_active = False

def apply_audio_effects(audio_data):
    """اعمال اثرات صوتی برای بهبود کیفیت"""
    global VOLUME
    
    # افزایش حجم صدا
    audio_data = audio_data * VOLUME
    
    # جلوگیری از clipping
    audio_data = np.clip(audio_data, -0.99, 0.99)
    
    # کاهش نویز
    if NOISE_REDUCTION:
        audio_data = np.convolve(audio_data.flatten(), np.hanning(5), mode='same').reshape(-1, 1)
    
    return audio_data

def audio_callback(indata, frames, time_info, status):
    global stream_active
    if not stream_active or not is_connected:
        return
    
    try:
        # پردازش صدا
        processed_audio = apply_audio_effects(indata)
        chunk = processed_audio.astype(AUDIO_FORMAT).tobytes()
        
        # فشرده‌سازی (اختیاری)
        chunk = audioop.lin2lin(chunk, 2, 2)
        chunk = audioop.ratecv(chunk, 2, CHANNELS, SAMPLE_RATE, SAMPLE_RATE, None)[0]
        
        sio.emit("audio_chunk", {
            "chunk": chunk,
            "sender_id": sender_id,
            "timestamp": time.time()
        })
    except Exception as e:
        print(f"Audio processing error: {str(e)}")

def start_stream():
    global stream_active
    
    # انتخاب بهترین دستگاه ورودی
    input_devices = [d for d in sd.query_devices() if d['max_input_channels'] > 0]
    input_device = input_devices[0]['index'] if input_devices else None
    
    stream_active = True
    print("🎤 شروع ارسال صدا با کیفیت بالا... (Ctrl+C برای توقف)")
    
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
    print("✓ متصل به سرور با کیفیت صوتی بالا")
    sio.emit("register_sender", {"sender_id": sender_id})

@sio.event
def disconnect():
    global is_connected
    is_connected = False
    print("✗ قطع ارتباط با سرور")

@sio.on("connection_ack")
def handle_ack(data):
    print(f"شناسه اتصال شما: {data['sid']}")
    print(f"تنظیمات سرور: نرخ نمونه‌برداری {data['config']['sample_rate']}Hz")

def main():
    try:
        print("🔊 در حال راه‌اندازی فرستنده صوتی با کیفیت...")
        print(f"شناسه فرستنده شما: {sender_id}")
        print(f"تنظیمات: نرخ نمونه‌برداری={SAMPLE_RATE}Hz, حجم صدا={VOLUME}x")
        
        sio.connect("https://h-musec.onrender.com", transports=['websocket'])
        start_stream()
    except KeyboardInterrupt:
        print("\nقطع ارتباط...")
    except Exception as e:
        print(f"خطا: {str(e)}")
    finally:
        sio.disconnect()

if __name__ == "__main__":
    main()