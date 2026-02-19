import time
import random
import os

LABELS = [
    "INFO", "WARNING", "ERROR", "CRITICAL"
]

USERS = ["root", "admin", "user", "guest", "service_account"]
IPS = ["192.168.1.5", "10.0.0.2", "203.0.113.4", "198.51.100.1"]

ATTACKS = [
    "Failed password for {user} from {ip} port 22 ssh2",
    "Accepted password for {user} from {ip} port 22 ssh2",
    "sudo: {user} : TTY=pts/0 ; PWD=/home/{user} ; USER=root ; COMMAND=/bin/bash",
    "Invalid user {user} from {ip}",
    "Received disconnect from {ip} port 22:11: Bye Bye [preauth]",
    "pam_unix(sshd:auth): authentication failure; logname= uid=0 euid=0 tty=ssh ruser= rhost={ip}  user={user}",
    "POST /login.php HTTP/1.1 401 Unauthorized - {ip}",
    "GET /etc/passwd HTTP/1.1 200 OK - {ip} (Possible LFI)",
    "SELECT * FROM users WHERE username = 'admin' OR '1'='1' -- (SQL Injection)",
    "honeypotd[9999]: ALERT: Tripwire triggered by {ip} on port 2121 (Honeypot FTP)"
]

def generate_log():
    template = random.choice(ATTACKS)
    user = random.choice(USERS)
    ip = random.choice(IPS)
    
    timestamp = time.strftime("%b %d %H:%M:%S")
    hostname = "ubuntu-server"
    
    log_line = f"{timestamp} {hostname} sshd[1234]: {template.format(user=user, ip=ip)}"
    return log_line

def main():
    print("[*] Starting Threat Simulator...")
    print("[*] Writing logs to test_log.txt (Press Ctrl+C to stop)")
    
    with open("test_log.txt", "a") as f:
        while True:
            log = generate_log()
            
            # Occasionally trigger a UEBA Brute Force burst
            if random.random() < 0.2:
                print("\n    [🚀 LAUNCHING BRUTE FORCE BURST]")
                bf_ip = random.choice(IPS)
                for _ in range(6):
                    bf_log = f"{time.strftime('%b %d %H:%M:%S')} ubuntu-server sshd[1234]: Failed password for root from {bf_ip} port 22 ssh2"
                    print(f"    -> Generated: {bf_log}")
                    f.write(bf_log + "\n")
                    f.flush()
                    time.sleep(0.1)
                print("    [BURST COMPLETE]\n")
            else:
                print(f"    -> Generated: {log}")
                f.write(log + "\n")
                f.flush()
            
            # Vary speed (sometimes fast burst, sometimes slow)
            time.sleep(random.uniform(0.5, 3.0))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Stopping simulator.")
