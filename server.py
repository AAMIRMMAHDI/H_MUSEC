import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from datetime import datetime
import time

app = Flask(__name__)

socketio = SocketIO(app,
                    cors_allowed_origins="*",
                    async_mode="eventlet",
                    ping_timeout=10,
                    ping_interval=5,
                    max_http_buffer_size=1e8)  # 100 MB

# کاربران متصل
senders = set()
receivers = set()
sid_to_sender = {}           # sid → sender_id
last_chunk_time = {}         # sid → last sent chunk timestamp

@app.route("/")
def index():
    return render_template("index.html",
                           senders=list(senders),
                           receivers=list(receivers),
                           ar=len(senders),
                           vr=len(receivers))

@socketio.on("connect")
def on_connect():
    sid = request.sid
    print(f"🟢 Client connected: {sid}")
    emit("connection_ack", {"status": "connected", "sid": sid})

@socketio.on("disconnect")
def on_disconnect():
    sid = request.sid
    print(f"🔴 Client disconnected: {sid}")
    senders.discard(sid)
    receivers.discard(sid)
    sid_to_sender.pop(sid, None)
    last_chunk_time.pop(sid, None)
    update_clients()

@socketio.on("register_sender")
def on_register_sender(data):
    sid = request.sid
    sender_id = data.get("sender_id", "unknown")
    senders.add(sid)
    sid_to_sender[sid] = sender_id
    print(f"🎤 Sender registered: {sid} as {sender_id}")
    update_clients()

@socketio.on("register_receiver")
def on_register_receiver():
    sid = request.sid
    receivers.add(sid)
    print(f"🎧 Receiver registered: {sid}")
    update_clients()

@socketio.on("audio_chunk")
def on_audio_chunk(data):
    sender_sid = request.sid

    # اطمینان از اینکه فرستنده معتبر است
    if sender_sid not in senders:
        return

    now = time.time()
    last_time = last_chunk_time.get(sender_sid, 0)

    # محدود کردن نرخ ارسال به 20 بار در ثانیه (50ms)
    if now - last_time < 0.05:
        return

    last_chunk_time[sender_sid] = now

    # پخش به همه‌ی گیرنده‌ها به صورت بهینه
    if receivers:
        emit("audio_stream", {
            "chunk": data.get("chunk"),
            "timestamp": now
        }, room=list(receivers), broadcast=True, include_self=False)

def update_clients():
    socketio.emit("user_update", {
        "ar": len(senders),
        "vr": len(receivers),
        "senders": list(senders),
        "receivers": list(receivers),
        "timestamp": datetime.now().isoformat()
    })

if __name__ == "__main__":
    print("🚀 Server running on http://0.0.0.0:5000")
    socketio.run(app, host="0.0.0.0", port=5000, debug=False)
