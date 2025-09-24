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
                    max_http_buffer_size=1e8)

senders = {}
receivers = set()

@app.route("/")
def index():
    return render_template("index.html",
                           senders=list(senders.values()),
                           receivers=list(receivers),
                           ar=len(senders),
                           vr=len(receivers))

@socketio.on("connect")
def handle_connect():
    sid = request.sid
    print(f"🟢 Connected: {sid}")
    emit("connection_ack", {"status": "connected", "sid": sid})

@socketio.on("disconnect")
def handle_disconnect():
    sid = request.sid
    senders.pop(sid, None)
    receivers.discard(sid)
    print(f"🔴 Disconnected: {sid}")
    update_clients()

@socketio.on("register_sender")
def handle_register_sender(data):
    sid = request.sid
    sender_id = data.get("sender_id", sid)
    senders[sid] = sender_id
    print(f"🎤 Sender registered: {sender_id}")
    update_clients()

@socketio.on("register_receiver")
def handle_register_receiver():
    sid = request.sid
    receivers.add(sid)
    print(f"🎧 Receiver registered: {sid}")
    update_clients()

@socketio.on("audio_chunk")
def handle_audio_chunk(data):
    sender_sid = request.sid
    chunk = data.get("chunk")

    # ارسال به همه گیرنده‌ها به جز خود فرستنده
    for receiver_sid in receivers:
        if receiver_sid != sender_sid:
            emit("audio_stream", {
                "chunk": chunk,
                "sender_id": senders.get(sender_sid, "unknown"),
                "timestamp": time.time()
            }, room=receiver_sid)

def update_clients():
    socketio.emit("user_update", {
        "ar": len(senders),
        "vr": len(receivers),
        "senders": list(senders.values()),
        "receivers": list(receivers),
        "timestamp": datetime.now().isoformat()
    })

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=False)