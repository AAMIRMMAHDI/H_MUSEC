import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

# لیست کاربران ارسال کننده و گیرنده
senders = set()
receivers = set()

@app.route("/")
def index():
    return render_template("index.html", senders=list(senders), receivers=list(receivers))

@socketio.on("connect")
def handle_connect():
    print(f"Client connected: {request.sid}")

@socketio.on("disconnect")
def handle_disconnect():
    sid = request.sid
    if sid in senders:
        senders.remove(sid)
    if sid in receivers:
        receivers.remove(sid)
    # آپدیت صفحه به همه
    socketio.emit("update_users", {"senders": list(senders), "receivers": list(receivers)})

@socketio.on("register_sender")
def register_sender():
    senders.add(request.sid)
    # بروز رسانی به همه
    socketio.emit("update_users", {"senders": list(senders), "receivers": list(receivers)})

@socketio.on("register_receiver")
def register_receiver():
    receivers.add(request.sid)
    socketio.emit("update_users", {"senders": list(senders), "receivers": list(receivers)})

@socketio.on("audio")
def handle_audio(data):
    # پخش صوت به همه گیرنده ها
    for r_sid in receivers:
        emit("audio", data, room=r_sid)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)
