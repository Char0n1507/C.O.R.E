import asyncio
import os
import signal
import sys
import yaml
from dotenv import load_dotenv
from core.ingestor import LogMonitor
from core.email_monitor import EmailMonitor
from core.analyzer import Analyzer
from core.database import Database
from modules.response.firewall import Firewall
from core.reporter import generate_daily_report
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
    print(rf"""{Colors.OKCYAN}{Colors.BOLD}
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
    
    # 2a. Start Email Monitor (Producer)
    email_config = config.get("sources", {}).get("email", {})
    email_monitor = EmailMonitor(email_config, log_queue, loop)
    email_task = asyncio.create_task(email_monitor.run())
    
    # 3. Start Analyzer (Consumer)
    # 3. Start Analyzer (Consumer)
    # Interactive AI Selection
    print(f"\n{Colors.OKCYAN}{Colors.BOLD}Select Intelligence Engine:{Colors.ENDC}")
    print(f"  {Colors.OKGREEN}[1]{Colors.ENDC} Google Gemini Pro (Cloud)")
    print(f"  {Colors.OKGREEN}[2]{Colors.ENDC} Local Ollama (Offline)")
    print(f"  {Colors.OKGREEN}[3]{Colors.ENDC} Rules-Based Engine Only")
    
    # Check for existing config or use default to avoid blocking in non-interactive shells
    default_choice = "3"
    if config.get("analyzer", {}).get("use_llm"):
        default_choice = "1" if config["analyzer"].get("provider") == "gemini" else "2"
    
    print(f"\n{Colors.OKCYAN}➔ Choose [1-3] (Default {default_choice}): {Colors.ENDC}", end="", flush=True)
    
    # Non-blocking input or use default if it fails (e.g. no TTY)
    try:
        import select
        if select.select([sys.stdin], [], [], 10)[0]:
            choice = sys.stdin.readline().strip()
        else:
            print(f"\n[!] Timeout: Using default choice ({default_choice})")
            choice = default_choice
    except:
        choice = default_choice
    
    if not choice:
        choice = default_choice
    
    if choice == '1':
        use_llm_mode = True
        llm_provider = "gemini"
    elif choice == '2':
        use_llm_mode = True
        llm_provider = "ollama"
    else:
        use_llm_mode = False
        llm_provider = "none"
        
    # Override config with user choice
    config["analyzer"]["use_llm"] = use_llm_mode
    config["analyzer"]["provider"] = llm_provider
    try:
        with open("config.yaml", "w") as f:
            yaml.dump(config, f, default_flow_style=False)
    except Exception as e:
        print(f"[!] Warning: Failed to save config.yaml: {e}")
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
    
    
    # Schedule Daily PDF Reporting
    print(f"{Colors.OKGREEN}[+] Automated Reporting engine loaded. PDF reports scheduled.{Colors.ENDC}")
    schedule.every().day.at("00:00").do(generate_daily_report)
    
    # Also generate an initial report to demonstrate the feature immediately
    generate_daily_report()
    
    async def schedule_loop():
        while True:
            schedule.run_pending()
            await asyncio.sleep(60)
            
    asyncio.create_task(schedule_loop())
    
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
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
