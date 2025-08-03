import socketio
import sounddevice as sd
import numpy as np
import time
import threading
from collections import deque
import audioop

# تنظیمات پیشرفته صدا
SAMPLE_RATE = 16000
CHANNELS = 1
BUFFER_SIZE = 256
AUDIO_FORMAT = 'int16'
OUTPUT_VOLUME = 1.5  # افزایش حجم صدا
BUFFER_DURATION = 0.15  # بافر برای جبران تأخیر شبکه (ثانیه)
EQUALIZER = True  # فعال کردن اکولایزر

sio = socketio.Client(reconnection_attempts=5, reconnection_delay=1)

audio_buffer = deque(maxlen=int(SAMPLE_RATE * BUFFER_DURATION / BUFFER_SIZE))
is_playing = False
last_chunk_time = 0

def apply_equalizer(audio_data):
    """اعمال اکولایزر برای بهبود کیفیت صدا"""
    if not EQUALIZER:
        return audio_data
    
    # تبدیل به فرکانس
    freq = np.fft.rfft(audio_data.flatten())
    samples = len(freq)
    
    # تقویت باندهای فرکانسی
    freq[:int(samples*0.1)] *= 1.2  # پایین‌ها
    freq[int(samples*0.1):int(samples*0.3)] *= 1.5  # میانه‌ها
    freq[int(samples*0.3):] *= 0.8  # بالاها
    
    # تبدیل برگشت
    return np.fft.irfft(freq).reshape(-1, 1)

def audio_callback(outdata, frames, time_info, status):
    global is_playing, last_chunk_time
    
    if not is_playing or len(audio_buffer) == 0:
        outdata.fill(0)
        return
    
    try:
        chunk = audio_buffer.popleft()
        
        # اعمال اکولایزر
        chunk = apply_equalizer(chunk)
        
        # افزایش حجم صدا
        chunk = chunk * OUTPUT_VOLUME
        
        # جلوگیری از clipping
        chunk = np.clip(chunk, -32768, 32767)
        
        outdata[:] = chunk
        last_chunk_time = time.time()
    except Exception as e:
        print(f"Playback error: {str(e)}")
        outdata.fill(0)

def playback_thread():
    global is_playing
    
    # انتخاب بهترین دستگاه خروجی
    output_devices = [d for d in sd.query_devices() if d['max_output_channels'] > 0]
    output_device = output_devices[0]['index'] if output_devices else None
    
    is_playing = True
    
    with sd.OutputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype=AUDIO_FORMAT,
        blocksize=BUFFER_SIZE,
        callback=audio_callback,
        device=output_device
    ):
        print("🔊 شروع پخش صدا با کیفیت بالا... (Ctrl+C برای توقف)")
        while is_playing:
            sd.sleep(100)

@sio.event
def connect():
    print("✓ متصل به سرور با کیفیت صوتی بالا")

@sio.event
def disconnect():
    print("✗ قطع ارتباط با سرور")

@sio.on("audio_stream")
def handle_audio(data):
    try:
        chunk = np.frombuffer(data["chunk"], dtype=AUDIO_FORMAT)
        chunk = chunk.reshape(-1, CHANNELS).astype('float32') / 32768.0
        
        # اگر بافر پر است، قدیمی‌ترین داده را حذف کن
        if len(audio_buffer) == audio_buffer.maxlen:
            audio_buffer.popleft()
            
        audio_buffer.append(chunk)
        
        # محاسبه تأخیر
        latency = time.time() - data["timestamp"]
        if latency > 0.3:  # فقط اگر تأخیر قابل توجه است چاپ کن
            print(f"تأخیر شبکه: {latency:.3f} ثانیه | فرستنده: {data['sender_id'][:8]}...")
    except Exception as e:
        print(f"Error processing audio: {str(e)}")

@sio.on("connection_ack")
def handle_ack(data):
    print(f"شناسه اتصال شما: {data['sid']}")
    print(f"تنظیمات سرور: نرخ نمونه‌برداری {data['config']['sample_rate']}Hz")

def main():
    try:
        print("🔈 در حال راه‌اندازی گیرنده صوتی با کیفیت...")
        print(f"تنظیمات: نرخ نمونه‌برداری={SAMPLE_RATE}Hz, حجم صدا={OUTPUT_VOLUME}x")
        
        # شروع پخش در یک رشته جداگانه
        play_thread = threading.Thread(target=playback_thread, daemon=True)
        play_thread.start()
        
        sio.connect("https://h-musec.onrender.com", transports=['websocket'])
        play_thread.join()
    except KeyboardInterrupt:
        print("\nقطع ارتباط...")
    except Exception as e:
        print(f"خطا: {str(e)}")
    finally:
        sio.disconnect()

if __name__ == "__main__":
    main()