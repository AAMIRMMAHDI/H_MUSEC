import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template
from flask_socketio import SocketIO, emit, request

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

senders = set()
receivers = set()
sid_to_sender = {}  # نگهداری شناسه یکتا برای هر ارسال‌کننده

@app.route("/")
def index():
    return render_template("index.html", senders=list(senders), receivers=list(receivers))

@socketio.on("connect")
def handle_connect():
    print(f"Client connected: {request.sid}")

@socketio.on("disconnect")
def handle_disconnect():
    sid = request.sid
    print(f"Client disconnected: {sid}")
    senders.discard(sid)
    receivers.discard(sid)
    sid_to_sender.pop(sid, None)
    socketio.emit("update_users", {
        "senders": list(senders),
        "receivers": list(receivers)
    })

@socketio.on("register_sender")
def register_sender(data):
    sid = request.sid
    sender_id = data.get("sender_id")
    senders.add(sid)
    sid_to_sender[sid] = sender_id
    print(f"Sender registered: {sid} as {sender_id}")
    socketio.emit("update_users", {
        "senders": list(senders),
        "receivers": list(receivers)
    })

@socketio.on("register_receiver")
def register_receiver():
    sid = request.sid
    receivers.add(sid)
    print(f"Receiver registered: {sid}")
    socketio.emit("update_users", {
        "senders": list(senders),
        "receivers": list(receivers)
    })

@socketio.on("audio")
def handle_audio(data):
    sender_id = data.get("sender_id")
    audio_data = data.get("audio")
    for r_sid in receivers:
        if sid_to_sender.get(r_sid) == sender_id:
            continue  # به خود فرستنده ارسال نکن
        emit("audio", audio_data, room=r_sid)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
