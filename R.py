import socketio
import sounddevice as sd
import numpy as np
import time
import threading
from collections import deque

# تنظیمات بهینه
sio = socketio.Client(reconnection_attempts=5, reconnection_delay=1)

# تنظیمات صدا
SAMPLE_RATE = 16000
CHANNELS = 1
BUFFER_SIZE = 256
AUDIO_FORMAT = 'int16'
MAX_BUFFER_DURATION = 0.2  # حداکثر 200ms بافر برای جبران تأخیر شبکه

audio_buffer = deque(maxlen=int(SAMPLE_RATE * MAX_BUFFER_DURATION / BUFFER_SIZE))
is_playing = False
last_chunk_time = 0

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

@sio.event
def connect():
    print("✓ متصل به سرور")
    sio.emit("register_receiver")

@sio.event
def disconnect():
    print("✗ قطع ارتباط با سرور")

@sio.on("audio_stream")
def handle_audio(data):
    try:
        chunk = np.frombuffer(data["chunk"], dtype=AUDIO_FORMAT)
        chunk = chunk.reshape(-1, CHANNELS)
        audio_buffer.append(chunk)
    except:
        pass

@sio.on("connection_ack")
def handle_ack(data):
    print(f"شناسه اتصال شما: {data['sid']}")

def main():
    try:
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