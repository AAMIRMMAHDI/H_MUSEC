import socketio
import sounddevice as sd
import numpy as np
import time
import threading
from collections import deque

# تنظیمات صدا
SAMPLE_RATE = 16000
CHANNELS = 1
BUFFER_SIZE = 256
AUDIO_FORMAT = 'int16'
OUTPUT_VOLUME = 1.5
BUFFER_DURATION = 0.15  # ثانیه

sio = socketio.Client(reconnection_attempts=5, reconnection_delay=1)

audio_buffer = deque(maxlen=int(SAMPLE_RATE * BUFFER_DURATION / BUFFER_SIZE))
is_playing = False
last_chunk_time = 0

def audio_callback(outdata, frames, time_info, status):
    global is_playing, last_chunk_time
    
    if not is_playing or len(audio_buffer) == 0:
        outdata.fill(0)
        return
    
    try:
        chunk = audio_buffer.popleft()
        chunk = (chunk * OUTPUT_VOLUME).clip(-32768, 32767)
        outdata[:] = chunk
        last_chunk_time = time.time()
    except:
        outdata.fill(0)

def playback_thread():
    global is_playing
    
    output_device = None
    try:
        output_devices = [d for d in sd.query_devices() if d['max_output_channels'] > 0]
        output_device = output_devices[0]['index'] if output_devices else None
    except:
        pass

    is_playing = True
    
    with sd.OutputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype=AUDIO_FORMAT,
        blocksize=BUFFER_SIZE,
        callback=audio_callback,
        device=output_device
    ):
        print("🔊 شروع پخش صدا... (Ctrl+C برای توقف)")
        print(f"تنظیمات: نرخ نمونه‌برداری={SAMPLE_RATE}Hz, حجم صدا={OUTPUT_VOLUME}x")
        while is_playing:
            sd.sleep(100)

@sio.event
def connect():
    print("✓ متصل به سرور آنلاین")
    sio.emit("register_receiver")

@sio.event
def disconnect():
    print("✗ قطع ارتباط با سرور")

@sio.on("audio_stream")
def handle_audio(data):
    try:
        chunk = np.frombuffer(data["chunk"], dtype=AUDIO_FORMAT)
        chunk = chunk.reshape(-1, CHANNELS).astype('float32') / 32768.0
        
        if len(audio_buffer) == audio_buffer.maxlen:
            audio_buffer.popleft()
            
        audio_buffer.append(chunk)
        
        latency = time.time() - data["timestamp"]
        if latency > 0.3:
            print(f"تأخیر شبکه: {latency:.3f} ثانیه")
    except Exception as e:
        print(f"خطای صدا: {str(e)}")

@sio.on("connection_ack")
def handle_ack(data):
    if 'config' in data:
        print(f"تنظیمات سرور: نرخ نمونه‌برداری {data['config']['sample_rate']}Hz")

def main():
    try:
        print("در حال اتصال به سرور آنلاین...")
        play_thread = threading.Thread(target=playback_thread, daemon=True)
        play_thread.start()
        
        sio.connect("https://h-musec.onrender.com", transports=['websocket'])
        play_thread.join()
    except KeyboardInterrupt:
        print("\nقطع ارتباط...")
    except Exception as e:
        print(f"خطا: {str(e)}")
        print("مطمئن شوید سرور آنلاین فعال است و اینترنت متصل است")
    finally:
        sio.disconnect()

if __name__ == "__main__":
    main()