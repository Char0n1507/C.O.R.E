import re
import subprocess
import logging

class Firewall:
    def __init__(self, dry_run=True):
        self.dry_run = dry_run
        self.blocked_ips = set()
        
    def extract_ip(self, text):
        """Extracts IPv4 address from text using regex."""
        ip_pattern = r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
        match = re.search(ip_pattern, text)
        if match:
            return match.group(1)
        return None

    def block_ip(self, ip, reason="High Risk Alert"):
        """
        Blocks an IP address using iptables (Linux).
        In dry_run mode, just logs the command.
        """
        if ip in self.blocked_ips:
            return False # Already blocked

        print(f"    [⚔️ ACTIVE DEFENSE] Initiating Block for {ip}...")
        
        cmd = ["sudo", "iptables", "-A", "INPUT", "-s", ip, "-j", "DROP", "-m", "comment", "--comment", f"SOC Agent: {reason}"]
        
        if self.dry_run:
            print(f"    [DRY RUN] Would execute: {' '.join(cmd)}")
            self.blocked_ips.add(ip)
            return True
        else:
            try:
                subprocess.run(cmd, check=True)
                print(f"    [SUCCESS] IP {ip} has been blocked at the firewall level.")
                self.blocked_ips.add(ip)
                return True
            except subprocess.CalledProcessError as e:
                print(f"    [ERROR] Failed to block IP: {e}")
                return False
            except PermissionError:
                print(f"    [ERROR] Permission denied. Run as root/sudo to block IPs.")
                return False
