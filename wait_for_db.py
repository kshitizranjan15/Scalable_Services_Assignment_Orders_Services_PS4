import os
import socket
import time

host = os.getenv("DB_HOST", "mysql_db")
port = int(os.getenv("DB_PORT", 3306))
timeout = int(os.getenv("DB_WAIT_TIMEOUT", 60))

def wait_host(h, p, t):
    for i in range(t):
        try:
            s = socket.create_connection((h, p), timeout=5)
            s.close()
            print(f"DB reachable at {h}:{p}")
            return True
        except Exception as e:
            print(f"Waiting for DB ({i+1}/{t})... {e}")
            time.sleep(1)
    return False

if __name__ == '__main__':
    if not wait_host(host, port, timeout):
        raise SystemExit(f"DB not reachable at {host}:{port}")
