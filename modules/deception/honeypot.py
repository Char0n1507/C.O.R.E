import socket
import time
import os
import threading

# Configuration
HONEYPOT_PORT = 2121  # Fake FTP Port
LOG_FILE = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "test_log.txt"))

def handle_connection(client_socket, address):
    ip, port = address
    timestamp = time.strftime("%b %d %H:%M:%S")
    
    # Log the malicious hit instantly
    log_entry = f"{timestamp} ubuntu-server honeypotd[9999]: ALERT: Tripwire triggered by {ip} on port {HONEYPOT_PORT} (Honeypot FTP)\n"
    
    print(f"[🍯 HONEYPOT] Tripwire triggered by {ip}!")
    
    with open(LOG_FILE, "a") as f:
        f.write(log_entry)
        f.flush()

    # Send a fake banner to keep them busy
    try:
        client_socket.send(b"220 ProFTPD 1.3.5 Server (ProFTPD)\r\n")
        time.sleep(2) # Fake delay
        client_socket.close()
    except Exception as e:
        print(f"Error handling connection: {e}")

def start_honeypot():
    # Ensure log file exists
    if not os.path.exists(LOG_FILE):
        open(LOG_FILE, 'w').close()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server.bind(("0.0.0.0", HONEYPOT_PORT))
        server.listen(5)
        print(f"[*] Honeypot Active. Trap set on port {HONEYPOT_PORT}...")
    except Exception as e:
        print(f"[!] Failed to bind port: {e}")
        return
    
    while True:
        try:
            client_socket, address = server.accept()
            client_thread = threading.Thread(target=handle_connection, args=(client_socket, address))
            client_thread.start()
        except KeyboardInterrupt:
            print("\n[!] Shutting down honeypot.")
            break

if __name__ == "__main__":
    start_honeypot()
