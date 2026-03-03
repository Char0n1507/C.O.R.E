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
    
    countries = ["China", "Russia", "United States", "Brazil", "Germany", "Iran", "North Korea", "India", "United Kingdom", "South Africa"]
    ips = [
        "114.114.114.114", "8.8.8.8", "200.200.200.200", "5.5.5.5", 
        "220.220.220.220", "150.150.150.150", "90.90.90.90", "120.120.120.120",
        "70.70.70.70", "180.180.180.180"
    ]
    tactics = ["Initial Access", "Execution", "Persistence", "Privilege Escalation", "Defense Evasion", "Credential Access", "Discovery", "Lateral Movement", "Collection", "Command and Control", "Exfiltration", "Impact"]
    actions = ["Logged", "Blocked by Firewall", "Quarantined", "Alerted SOC"]
    users = ["root", "admin", "system", "postgres", "guest", "ubuntu", "nginx", "apache"]
    
    print("Pumping 150 diverse alerts into the Enterprise DB...")
    
    for _ in range(150):
        country = random.choice(countries)
        ip = random.choice(ips)
        tactic = random.choice(tactics)
        action = random.choice(actions)
        user = random.choice(users)
        risk_score = random.randint(40, 100)
        
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
            "action": action
        }
        
        # Save to DB
        db.save_alert(target_payload)

    print("Successfully pumped data!")

if __name__ == "__main__":
    generate_lively_data()
