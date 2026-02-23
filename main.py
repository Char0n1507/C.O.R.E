import asyncio
import os
import yaml
import time
from datetime import datetime
from core.ingestor import LogMonitor
from core.ingestor_enterprise import EnterpriseKafkaMonitor
from core.email_monitor import EmailMonitor
from core.analyzer import Analyzer
from core.database_enterprise import EnterpriseDatabase
from modules.response.firewall import Firewall
from modules.response.remote_response import RemoteResponder
from core.ingestor_webhook import WebhookIngestor
from core.reporter import generate_daily_report
from modules.deception.honeypot import CyberDeception
import schedule

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_banner():
    banner = f"""{Colors.OKCYAN}
   ____   ___  ____  _____ 
  / ___| / _ \|  _ \| ____|
 | |    | | | | |_) |  _|  
 | |___ | |_| |  _ <| |___ 
  \\____| \\___/|_| \\_\\_____|
                           
  AI SOC AGENT: C.O.R.E. v2.0
  ------------------------------------------------{Colors.ENDC}"""
    print(banner)

async def main():
    print_banner()
    
    # Load Config
    try:
        with open("config.yaml", "r") as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"{Colors.FAIL}[!] Critical Error: Could not load config.yaml ({e}){Colors.ENDC}")
        return

    print(f"[*] Initializing Command Center...")
    
    # 0. Database
    db = EnterpriseDatabase()
    print(f"{Colors.OKGREEN}[+] Infrastructure: PostgreSQL Active{Colors.ENDC}")
    
    # 0a. Response
    dry_run_mode = config.get("response", {}).get("dry_run", True)
    firewall = Firewall(dry_run=dry_run_mode)
    remote_responder = RemoteResponder(config)
    print(f"{Colors.OKGREEN}[+] Defense: {'Local & Remote (Simulated)' if dry_run_mode else 'LIVE ACTIVE RESPONSE'}{Colors.ENDC}")

    # 1. Processing Queue
    log_queue = asyncio.Queue()
    loop = asyncio.get_event_loop()

    # 2. Start Ingestors
    # Kafka
    kafka_server = "localhost:9092"
    kafka_monitor = EnterpriseKafkaMonitor(kafka_server, ["enterprise-logs"], log_queue, loop)
    kafka_monitor.start()
    
    # Local File Monitor
    log_paths = config.get("sources", {}).get("logs", [])
    if log_paths:
        file_monitor = LogMonitor(log_paths, log_queue, loop)
        file_monitor.start()

    # Webhook
    webhook_port = config.get("sources", {}).get("webhook_port", 8080)
    webhook_ingestor = WebhookIngestor(port=webhook_port, processing_queue=log_queue, loop=loop)
    webhook_ingestor.start()

    # Email
    email_config = config.get("sources", {}).get("email", {})
    email_monitor = EmailMonitor(email_config, log_queue, loop)
    asyncio.create_task(email_monitor.run())

    # 2a. Deception Engine
    deception_engine = CyberDeception(config, log_queue, loop)
    deception_engine.start()
    print(f"{Colors.OKGREEN}[+] Infrastructure: Cyber Deception Engine Active (Ghost Nodes Deployed){Colors.ENDC}")

    # 3. Intelligence Selection
    print(f"\n{Colors.BOLD}Select Intelligence Engine:{Colors.ENDC}")
    provider = config.get('analyzer', {}).get('provider', 'rules')
    use_llm = config.get('analyzer', {}).get('use_llm', False)
    
    print(f"  [1] Google Gemini Pro (Cloud)")
    print(f"  [2] Local Ollama (Offline)")
    print(f"  [3] Rules-Based Engine Only")
    
    # Use config as default
    engine_display = {
        "gemini": "Google Gemini Pro",
        "ollama": "Local Ollama",
        "rules": "Standard Rules"
    }
    print(f"➔ Intelligence Engine: {Colors.OKCYAN}{engine_display.get(provider, 'Standard Rules')}{Colors.ENDC}")
    
    analyzer = Analyzer(config)
    
    print(f"\n{Colors.OKBLUE}=================================================================={Colors.ENDC}")
    print(f"{Colors.BOLD}[✓] C.O.R.E. IS ONLINE & MONITORING TRAFFIC{Colors.ENDC}")
    print(f"{Colors.OKBLUE}=================================================================={Colors.ENDC}\n")

    # 4. Main Loop
    while True:
        log_entry = await log_queue.get()
        if log_entry:
            result = await analyzer.analyze_log(log_entry)
            
            # Simplified & Action-Oriented Terminal Interface
            risk = result.get('risk_score', 0)
            if risk >= 50:
                color = Colors.FAIL if risk >= 90 else Colors.WARNING
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                print(f"{color}[{timestamp}] 🚨 THREAT DETECTED (Risk: {risk}/100){Colors.ENDC}")
                print(f"    🔎 Analysis : {result['analysis']}")
                print(f"    📦 Source   : {result['source']}")
                
                # Active Actions
                threshold = config.get("response", {}).get("block_threshold", 90)
                if risk >= threshold:
                    ip = firewall.extract_ip(result['raw_content'])
                    if ip:
                        print(f"    🛡️  Defense  : Automatically blocking {ip}...")
                        firewall.block_ip(ip, reason=result['analysis'])
                        await remote_responder.execute_action("REMOTELY_BLOCK_IP", ip, reason=result['analysis'])
                print("") # Spacer

            # Persistence
            db.save_alert(result)
        log_queue.task_done()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}[!] SOC Shutting down...{Colors.ENDC}")
