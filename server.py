import socket
import threading
import json
import struct  # برای pack/unpack length
from datetime import datetime
import time

# تنظیمات سرور (مثل قبل)
HOST = '0.0.0.0'
PORT = 5000

senders = {}
receivers = set()
client_sockets = {}

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen(5)
print(f"Server listening on {HOST}:{PORT}")

def handle_client(client_socket, address):
    sid = f"{address[0]}:{address[1]}"
    print(f"🟢 Connected: {sid}")
    client_sockets[sid] = client_socket

    try:
        while True:
            # دریافت داده با header (اول length، بعد JSON یا binary)
            length_data = client_socket.recv(4)
            if len(length_data) < 4:
                break
            length = struct.unpack('!I', length_data)[0]  # unsigned int big-endian
            data = b''
            while len(data) < length:
                packet = client_socket.recv(length - len(data))
                if not packet:
                    break
                data += packet
            if not data:
                break

            # اگر JSON باشه (برای register)، parse کن
            if len(data) < 100:  # حدس ساده: JSON کوچیکه
                try:
                    message = json.loads(data.decode('utf-8'))
                    handle_message(client_socket, sid, message)
                except json.JSONDecodeError:
                    print(f"Invalid JSON from {sid}: {data}")
            else:
                # binary audio chunk: forward به receivers
                handle_audio_chunk(client_socket, sid, data)

    except Exception as e:
        print(f"Error handling client {sid}: {e}")
    finally:
        client_socket.close()
        senders.pop(sid, None)
        receivers.discard(sid)
        client_sockets.pop(sid, None)
        print(f"🔴 Disconnected: {sid}")
        update_clients()

def handle_message(client_socket, sid, message):
    action = message.get("action")
    if action == "register_sender":
        sender_id = message.get("sender_id", sid)
        senders[sid] = sender_id
        print(f"🎤 Sender registered: {sender_id}")
        client_socket.send(struct.pack('!I', len(json.dumps({"action": "connection_ack", "sid": sid}).encode('utf-8'))) + json.dumps({"action": "connection_ack", "sid": sid}).encode('utf-8'))
        update_clients()
    elif action == "register_receiver":
        receivers.add(sid)
        print(f"🎧 Receiver registered: {sid}")
        client_socket.send(struct.pack('!I', len(json.dumps({"action": "connection_ack", "sid": sid}).encode('utf-8'))) + json.dumps({"action": "connection_ack", "sid": sid}).encode('utf-8'))
        update_clients()

def handle_audio_chunk(sender_socket, sid, chunk_bytes):
    """Forward binary chunk به receivers"""
    sender_id = senders.get(sid, "unknown")
    timestamp = time.time()
    
    # ساخت پیام binary: header JSON + chunk
    json_part = json.dumps({
        "action": "audio_stream",
        "sender_id": sender_id,
        "timestamp": timestamp
    }).encode('utf-8')
    full_message = json_part + b'|' + chunk_bytes  # separator ساده
    
    for receiver_sid in receivers:
        if receiver_sid != sid and receiver_sid in client_sockets:
            try:
                receiver_sock = client_sockets[receiver_sid]
                header = struct.pack('!I', len(full_message))
                receiver_sock.send(header + full_message)
            except Exception as e:
                print(f"Error sending to {receiver_sid}: {e}")

def update_clients():
    update_message = json.dumps({
        "action": "user_update",
        "ar": len(senders),
        "vr": len(receivers),
        "senders": list(senders.values()),
        "receivers": list(receivers),
        "timestamp": datetime.now().isoformat()
    }).encode('utf-8')
    header = struct.pack('!I', len(update_message))
    
    for sid, client_socket in client_sockets.items():
        try:
            client_socket.send(header + update_message)
        except Exception as e:
            print(f"Error updating {sid}: {e}")

def accept_connections():
    while True:
        client_socket, address = server_socket.accept()
        threading.Thread(target=handle_client, args=(client_socket, address), daemon=True).start()

if __name__ == "__main__":
    threading.Thread(target=accept_connections, daemon=True).start()
    print("Server started. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down server...")
        server_socket.close()