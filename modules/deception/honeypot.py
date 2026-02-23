import logging
import random
import time
from datetime import datetime

class CyberDeception:
    def __init__(self, config, log_queue, loop):
        self.config = config.get("deception", {})
        self.enabled = self.config.get("enabled", True)
        self.log_queue = log_queue
        self.loop = loop
        self.decoys = [
            {"name": "FINANCIAL_DB_EXCEL_EXPORT", "type": "file_lure", "path": "/data/exports/q4_finance.xlsx"},
            {"name": "ADMIN_VPN_PORTAL_STAGING", "type": "network_lure", "port": 8443},
            {"name": "LEGACY_DEVELOPMENT_API", "type": "api_lure", "endpoint": "/api/v1/debug/dump_config"},
            {"name": "SYSTEM_ROOT_CREDENTIALS_BACKUP", "type": "credential_lure", "user": "admin_backup"}
        ]
        self.active_decoys = []

    def start(self):
        if not self.enabled:
            return
        
        logging.info("[🎭 DECEPTION] Initializing Ghost Nodes and Decoy Lures...")
        # In a real environment, this might actually open ports or create files.
        # Here we simulate the "Tripwire" monitoring of these lures.
        self.active_decoys = random.sample(self.decoys, 2)
        for decoy in self.active_decoys:
            logging.info(f"[🎭 DECEPTION] Deployed Ghost Node: {decoy['name']} ({decoy['type']})")

    def simulate_touch(self, ip="192.168.1.100"):
        """Simulates an attacker interacting with a decoy."""
        decoy = random.choice(self.active_decoys)
        
        # Create a 'High Confidence' log entry
        log_entry = {
            "timestamp": int(time.time()),
            "ip": ip,
            "source": "DECEPTION_ENGINE",
            "raw_content": f"GHOST_NODE_TRIPWIRE: Interaction detected on {decoy['name']} ({decoy['type']}) from {ip}",
            "mitre_tactic": "Discovery",
            "risk_score": 100, # 100% confidence because it's a honeypot
            "analysis": f"CRITICAL: Attacker interacted with decoy {decoy['name']}. This is indicative of lateral movement or discovery phases.",
            "action": "AUTO_LOCKDOWN_RESOURCES"
        }
        
        if self.loop:
            self.loop.call_soon_threadsafe(self.log_queue.put_nowait, log_entry)
        return log_entry
