import asyncio
import os
import signal
import sys
import yaml
from dotenv import load_dotenv
from core.ingestor import LogMonitor
from core.analyzer import Analyzer
from core.database import Database
from modules.response.firewall import Firewall

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

# Load env vars
load_dotenv()

# Load configuration
try:
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
except FileNotFoundError:
    print("[!] config.yaml not found! Using default variables.")
    config = {
        "agent": {"name": "C.O.R.E."},
        "sources": {"logs": ["test_log.txt"]},
        "response": {"dry_run": True, "block_threshold": 90},
        "analyzer": {"use_llm": False}
    }

LOG_PATHS = config.get("sources", {}).get("logs", ["test_log.txt"])

async def main():
    agent_name = config.get("agent", {}).get("name", "C.O.R.E.")
    print(f"""{Colors.OKCYAN}{Colors.BOLD}
   ____   ___  ____  _____ 
  / ___| / _ \|  _ \| ____|
 | |    | | | | |_) |  _|  
 | |___ | |_| |  _ <| |___ 
  \____| \___/|_| \_\_____|
                           
  AI SOC AGENT: {agent_name}
  {Colors.ENDC}{Colors.OKBLUE}------------------------------------------------{Colors.ENDC}
    """)
    print(f"{Colors.OKCYAN}[*] Initializing Core Modules...{Colors.ENDC}")
    
    # 0. Database
    db = Database()
    print(f"{Colors.OKGREEN}[+] Connected to Alert Database (soc_agent.db){Colors.ENDC}")
    
    # 0a. Active Response
    dry_run_mode = config.get("response", {}).get("dry_run", True)
    firewall = Firewall(dry_run=dry_run_mode)
    print(f"{Colors.OKGREEN}[+] Active Response Module Initialized (Mode: {'DRY RUN' if dry_run_mode else 'LIVE'}){Colors.ENDC}")
    
    # 1. Processing Queue (Logs -> Q -> Analyzer)
    log_queue = asyncio.Queue()
    loop = asyncio.get_running_loop()
    
    # 2. Start Log Monitor (Producer)
    monitor = LogMonitor(LOG_PATHS, log_queue, loop)
    monitor.start()
    
    # 3. Start Analyzer (Consumer)
    use_llm_mode = config.get("analyzer", {}).get("use_llm", False)
    llm_provider = config.get("analyzer", {}).get("provider", "gemini")
    ollama_url = config.get("analyzer", {}).get("ollama_url", "http://localhost:11434")
    ollama_model = config.get("analyzer", {}).get("ollama_model", "llama3")
    
    analyzer = Analyzer(
        use_llm=use_llm_mode,
        provider=llm_provider,
        ollama_url=ollama_url,
        ollama_model=ollama_model
    )
    
    print(f"{Colors.HEADER}{Colors.BOLD}=================================================================={Colors.ENDC}")
    print(f"{Colors.OKGREEN}[✓] C.O.R.E. is now monitoring logs for threats. Press Ctrl+C to stop.{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}=================================================================={Colors.ENDC}")
    
    try:
        while True:
            # Consume new logs
            log_event = await log_queue.get()
            
            # Analyze using AI/Rules
            result = await analyzer.analyze_log(log_event)
            
            # Print alerts for high risk events
            if result['risk_score'] > 50:
                print(f"\n{Colors.FAIL}{Colors.BOLD}[🚨 THREAT DETECTED - RISK {result['risk_score']}]{Colors.ENDC} {Colors.WARNING}{result.get('analysis', 'Unknown Threat')}{Colors.ENDC}")
                if 'action' in result:
                    print(f"    {Colors.OKCYAN}➔ [ACTION]   :{Colors.ENDC} {result['action']}")
                print(f"    {Colors.OKBLUE}➔ [SOURCE]   :{Colors.ENDC} {result['source']}")
                print(f"    {Colors.OKBLUE}➔ [RAW LOG]  :{Colors.ENDC} {result['raw_content']}")
                
                # Active Response Logic
                threshold = config.get("response", {}).get("block_threshold", 90)
                if result['risk_score'] >= threshold:
                    ip = firewall.extract_ip(result['raw_content'])
                    if ip:
                        firewall.block_ip(ip, reason=result['analysis'])
                
                # Save to DB
                db.save_alert(result)
            
            # Mark task as done
            log_queue.task_done()
            
    except asyncio.CancelledError:
        print("[!] Stopping...")
    finally:
        monitor.stop()

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        sys.exit(0)
