import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from flask import request

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

senders = set()
receivers = set()

@app.route("/")
def index():
    # صفحه اصلی با لیست فرستنده‌ها و گیرنده‌ها
    return render_template("index.html", senders=list(senders), receivers=list(receivers))

@socketio.on("connect")
def handle_connect():
    sid = request.sid
    print(f"Client connected: {sid}")

@socketio.on("disconnect")
def handle_disconnect():
    sid = request.sid
    print(f"Client disconnected: {sid}")
    if sid in senders:
        senders.remove(sid)
    if sid in receivers:
        receivers.remove(sid)
    socketio.emit("update_users", {"senders": list(senders), "receivers": list(receivers)})

@socketio.on("register_sender")
def register_sender():
    sid = request.sid
    senders.add(sid)
    print(f"Sender registered: {sid}")
    socketio.emit("update_users", {"senders": list(senders), "receivers": list(receivers)})

@socketio.on("register_receiver")
def register_receiver():
    sid = request.sid
    receivers.add(sid)
    print(f"Receiver registered: {sid}")
    socketio.emit("update_users", {"senders": list(senders), "receivers": list(receivers)})

@socketio.on("audio")
def handle_audio(data):
    sid = request.sid
    # ارسال داده صوتی به تمام گیرنده‌ها به جز خود فرستنده
    for r_sid in receivers:
        if r_sid != sid:
            emit("audio", data, room=r_sid)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
