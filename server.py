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
                   ping_timeout=5,
                   ping_interval=2,
                   max_http_buffer_size=1e8)

senders = set()
receivers = set()
sid_to_sender = {}
connection_times = {}

@app.route("/")
def index():
    return render_template("index.html", 
                         senders=list(senders), 
                         receivers=list(receivers),
                         ar=len(senders),
                         vr=len(receivers))

@socketio.on("connect")
def handle_connect():
    sid = request.sid
    connection_times[sid] = time.time()
    print(f"Client connected: {sid}")
    emit("connection_ack", {"status": "connected", "sid": sid})

@socketio.on("disconnect")
def handle_disconnect():
    sid = request.sid
    print(f"Client disconnected: {sid}")
    senders.discard(sid)
    receivers.discard(sid)
    sid_to_sender.pop(sid, None)
    connection_times.pop(sid, None)
    update_clients()

@socketio.on("register_sender")
def register_sender(data):
    sid = request.sid
    sender_id = data.get("sender_id")
    senders.add(sid)
    sid_to_sender[sid] = sender_id
    print(f"Sender registered: {sid} as {sender_id}")
    update_clients()

@socketio.on("register_receiver")
def register_receiver():
    sid = request.sid
    receivers.add(sid)
    print(f"Receiver registered: {sid}")
    update_clients()

@socketio.on("audio_chunk")
def handle_audio_chunk(data):
    sender_sid = request.sid
    if sender_sid not in senders:
        return
        
    # ارسال به همه گیرنده‌ها به جز خود فرستنده
    for receiver_sid in receivers:
        if receiver_sid != sender_sid:
            emit("audio_stream", {
                "chunk": data["chunk"],
                "timestamp": time.time()
            }, room=receiver_sid)

def update_clients():
    socketio.emit("user_update", {
        "ar": len(senders),
        "vr": len(receivers),
        "senders": list(senders),
        "receivers": list(receivers),
        "timestamp": datetime.now().isoformat()
    })

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)