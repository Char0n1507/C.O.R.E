import sys
import os
from datetime import datetime
import random

# Path Setup for Enterprise Logic
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)
from core.database_enterprise import EnterpriseDatabase

def generate_lively_data():
    db = EnterpriseDatabase()
    
    countries = ["China", "Russia", "United States", "Brazil", "Germany", "Iran", "North Korea", "India", "United Kingdom", "South Africa", "Japan", "South Korea"]
    ips = [
        "114.114.114.114", "8.8.8.8", "200.200.200.200", "5.5.5.5", 
        "220.220.220.220", "150.150.150.150", "90.90.90.90", "120.120.120.120",
        "70.70.70.70", "180.180.180.180", "12.34.56.78", "88.99.11.22"
    ]
    tactics = ["Initial Access", "Execution", "Persistence", "Privilege Escalation", "Defense Evasion", "Credential Access", "Discovery", "Lateral Movement", "Collection", "Command and Control", "Exfiltration", "Impact"]
    actions = ["Logged", "Blocked by Firewall", "Quarantined", "Alerted SOC", "AUTO_LOCKDOWN_RESOURCES"]
    users = ["root", "admin", "system", "postgres", "guest", "ubuntu", "nginx", "apache"]
    
    print("Pumping 500 diverse alerts into the Enterprise DB to make the dashboard lively...")
    
    for i in range(500):
        country = random.choice(countries)
        ip = random.choice(ips)
        tactic = random.choice(tactics)
        action = random.choice(actions)
        user = random.choice(users)
        risk_score = random.randint(30, 100)
        
        # Randomly generate Deception Engine / Ghost Node logs
        is_deception = random.random() < 0.15 # 15% chance to be a deception event
        
        if is_deception:
            source = "DECEPTION_ENGINE"
            raw_content = f"GHOST_NODE_TRIPWIRE: Interaction detected on FINANCIAL_DB_EXCEL_EXPORT from {ip} (Unauthorized access attempt)"
            analysis = f"CRITICAL breach: Attacker {ip} interacted with Ghost Node FINANCIAL_DB_EXCEL_EXPORT."
            risk_score = 100
            tactic = "Discovery"
            action = "AUTO_LOCKDOWN_RESOURCES"
            country = "Unknown" 
        else:
            source = random.choice(["kafka://enterprise-logs", "/var/log/syslog", "/var/log/auth.log"])
            raw_content = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Failed password for {user} from {ip} port {random.randint(1024, 65535)} ssh2"
            analysis = f"Detected {tactic} attempt from {country} targeting {user} account."
        
        target_payload = {
            "timestamp": datetime.now(),
            "ip": ip,
            "port": random.randint(22, 443),
            "threat_type": tactic,
            "risk_score": risk_score,
            "analysis": analysis,
            "raw_content": raw_content,
            "country": country,
            "mitre_tactic": tactic,
            "action": action,
            "source": source
        }
        
        # Save to DB
        db.save_alert(target_payload)

    print("Successfully pumped 500 alerts!")

if __name__ == "__main__":
    generate_lively_data()
