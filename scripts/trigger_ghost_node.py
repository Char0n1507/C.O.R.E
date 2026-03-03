from core.database_enterprise import EnterpriseDatabase
import time
from datetime import datetime

def trigger():
    db = EnterpriseDatabase()
    
    # Simulate a Ghost Node interaction
    decoy_name = "FINANCIAL_DB_EXCEL_EXPORT"
    attacker_ip = "10.99.88.77"
    
    alert_data = {
        "timestamp": str(time.time()),
        "source": "DECEPTION_ENGINE",
        "risk_score": 100,
        "analysis": f"CRITICAL breach: Attacker {attacker_ip} interacted with Ghost Node {decoy_name}.",
        "action": "AUTO_LOCKDOWN_RESOURCES",
        "raw_content": f"GHOST_NODE_TRIPWIRE: Interaction detected on {decoy_name} from {attacker_ip}",
        "country": "Unauthorized",
        "city": "Unknown",
        "lat": 0.0,
        "lon": 0.0,
        "alpha_3": "N/A",
        "ip": attacker_ip,
        "mitre_tactic": "Discovery",
        "mitre_technique": "Honeypot Interaction"
    }
    
    print(f"[*] Triggering Ghost Node breach for {decoy_name}...")
    alert_id = db.save_alert(alert_data)
    print(f"[✓] Deception alert logged (ID: {alert_id}). Check the GHOST NODES tab on the dashboard!")

if __name__ == "__main__":
    trigger()
