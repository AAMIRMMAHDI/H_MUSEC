import socket
import threading
import struct

HOST = "0.0.0.0"
PORT = 5000

clients = []  # لیست همه گیرنده‌ها

def handle_client(conn, addr):
    print(f"🟢 اتصال جدید: {addr}")
    try:
        while True:
            # خواندن طول chunk (۴ بایت)
            length_data = conn.recv(4)
            if not length_data:
                break

            length = struct.unpack(">I", length_data)[0]
            data = b""
            while len(data) < length:
                packet = conn.recv(length - len(data))
                if not packet:
                    break
                data += packet

            if not data:
                break

            # ارسال داده به تمام گیرنده‌ها به جز فرستنده
            for c in clients:
                if c != conn:
                    try:
                        c.sendall(length_data + data)
                    except:
                        pass
    except Exception as e:
        print(f"✗ خطای ارتباط با {addr}: {e}")
    finally:
        if conn in clients:
            clients.remove(conn)
        conn.close()
        print(f"🔴 اتصال بسته شد: {addr}")

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(10)
    print(f"🚀 سرور TCP در حال اجرا روی {HOST}:{PORT}")

    try:
        while True:
            conn, addr = server.accept()
            clients.append(conn)
            thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            thread.start()
    except KeyboardInterrupt:
        print("\n⛔ سرور متوقف شد")
    finally:
        server.close()

if __name__ == "__main__":
    main()
