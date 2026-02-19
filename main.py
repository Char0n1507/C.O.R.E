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
    print(f"""
    AI SOC AGENT: {agent_name}
    ------------------------
    [+] Initializing Core Modules...
    """)
    
    # 0. Database
    db = Database()
    print("[+] Connected to Alert Database (soc_agent.db)")
    
    # 0a. Active Response
    dry_run_mode = config.get("response", {}).get("dry_run", True)
    firewall = Firewall(dry_run=dry_run_mode)
    print(f"[+] Active Response Module Initialized (Mode: {'DRY RUN' if dry_run_mode else 'LIVE'})")
    
    # 1. Processing Queue (Logs -> Q -> Analyzer)
    log_queue = asyncio.Queue()
    loop = asyncio.get_running_loop()
    
    # 2. Start Log Monitor (Producer)
    monitor = LogMonitor(LOG_PATHS, log_queue, loop)
    monitor.start()
    
    # 3. Start Analyzer (Consumer)
    use_llm_mode = config.get("analyzer", {}).get("use_llm", False)
    analyzer = Analyzer(use_llm=use_llm_mode)
    
    print("[+] Agent is now monitoring logs for threats. Press Ctrl+C to stop.")
    
    try:
        while True:
            # Consume new logs
            log_event = await log_queue.get()
            
            # Analyze using AI/Rules
            result = await analyzer.analyze_log(log_event)
            
            # Print alerts for high risk events
            if result['risk_score'] > 50:
                print(f"\n[ALERT - RISK {result['risk_score']}] {result.get('analysis', 'Unknown Threat')}")
                if 'action' in result:
                    print(f"    [ACTION RECOMMENDED]: {result['action']}")
                print(f"    Source: {result['source']}")
                print(f"    Raw: {result['raw_content']}")
                
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
