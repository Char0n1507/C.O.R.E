import asyncio
import os
import sys
import yaml
import time
import subprocess
from datetime import datetime

# Core Modules
from core.ingestor import LogMonitor
from core.ingestor_enterprise import EnterpriseKafkaMonitor
from core.email_monitor import EmailMonitor
from core.analyzer import Analyzer
from core.database_enterprise import EnterpriseDatabase
from modules.response.firewall import Firewall
from modules.response.remote_response import RemoteResponder
from core.ingestor_webhook import WebhookIngestor
from modules.deception.honeypot import CyberDeception
from core.ingestor_wifi import NetworkPacketMonitor
from core.threat_sim import ThreatSimulator
from dotenv import load_dotenv

# Load Environment Variables
load_dotenv()


# --- UI CONSTANTS ---
class Colors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def print_banner():
    os.system("clear")
    banner = rf"""{Colors.OKCYAN}
   ____   ___  ____  _____ 
  / ___| / _ \|  _ \| ____|
 | |    | | | | |_) |  _|  
 | |___ | |_| |  _ <| |___ 
  \____| \___/|_| \_\_____|
                           
   {Colors.BOLD}MASTER CONTROL CENTER v2.5{Colors.ENDC} {Colors.OKCYAN}
  ------------------------------------------------{Colors.ENDC}"""
    print(banner)


def print_capabilities():
    print(
        f"{Colors.OKCYAN}┌────────────────────────────────────────────────┐{Colors.ENDC}"
    )
    print(
        f"{Colors.OKCYAN}│{Colors.ENDC}  {Colors.BOLD}Ecosystem Architecture & Capabilities:{Colors.ENDC}          {Colors.OKCYAN}│{Colors.ENDC}"
    )
    print(
        f"{Colors.OKCYAN}├────────────────────────────────────────────────┤{Colors.ENDC}"
    )
    print(
        f"{Colors.OKCYAN}│{Colors.ENDC}  {Colors.OKGREEN}►{Colors.ENDC}  {Colors.BOLD}🧠 AI Analyst{Colors.ENDC} : Gemini Pro Deep Analysis     {Colors.OKCYAN}│{Colors.ENDC}"
    )
    print(
        f"{Colors.OKCYAN}│{Colors.ENDC}  {Colors.OKGREEN}►{Colors.ENDC}  {Colors.BOLD}🛡️  Response{Colors.ENDC}   : LIVE Autonomous Blocking      {Colors.OKCYAN}│{Colors.ENDC}"
    )
    print(
        f"{Colors.OKCYAN}│{Colors.ENDC}  {Colors.OKGREEN}►{Colors.ENDC}  {Colors.BOLD}🕸️  Deception{Colors.ENDC}  : Active Ghost Node Network      {Colors.OKCYAN}│{Colors.ENDC}"
    )
    print(
        f"{Colors.OKCYAN}│{Colors.ENDC}  {Colors.OKGREEN}►{Colors.ENDC}  {Colors.BOLD}📡 Sniffing{Colors.ENDC}   : Raw L2/WiFi Traffic Monitor   {Colors.OKCYAN}│{Colors.ENDC}"
    )
    print(
        f"{Colors.OKCYAN}│{Colors.ENDC}  {Colors.OKGREEN}►{Colors.ENDC}  {Colors.BOLD}📊 Control{Colors.ENDC}    : Real-time Mission Dash (8501) {Colors.OKCYAN}│{Colors.ENDC}"
    )
    print(
        f"{Colors.OKCYAN}│{Colors.ENDC}  {Colors.OKGREEN}►{Colors.ENDC}  {Colors.BOLD}🕵️  Red Team{Colors.ENDC}   : Integrated Threat Simulation  {Colors.OKCYAN}│{Colors.ENDC}"
    )
    print(
        f"{Colors.OKCYAN}└────────────────────────────────────────────────┘{Colors.ENDC}"
    )


# --- GLOBAL PROCESS MANAGEMENT ---
background_subprocesses = []


async def run_maintenance(db):
    """Handles daily database cleanup tasks at 23:59."""
    while True:
        now = datetime.now()
        if now.hour == 23 and now.minute == 59:
            print(
                f"\n{Colors.WARNING}[!] UNIFIED CTRL: Resetting Dashboard for the new day...{Colors.ENDC}",
                flush=True,
            )
            db.clear_all_alerts()
            await asyncio.sleep(61)
        await asyncio.sleep(30)


async def core_engine(mode, config):
    print(f"\n{Colors.OKBLUE}[*] Initializing Command Center...{Colors.ENDC}")

    # 0. Database
    db = EnterpriseDatabase()
    print(f"{Colors.OKGREEN}[+] Infrastructure: PostgreSQL Active{Colors.ENDC}")

    # 0a. Response
    dry_run_mode = config.get("response", {}).get("dry_run", True)
    firewall = Firewall(dry_run=dry_run_mode)
    remote_responder = RemoteResponder(config)
    print(
        f"{Colors.OKGREEN}[+] Defense: {'Local & Remote (Simulated)' if dry_run_mode else 'LIVE ACTIVE RESPONSE'}{Colors.ENDC}"
    )

    # 1. Processing Queue
    log_queue = asyncio.Queue()
    loop = asyncio.get_event_loop()

    # 2. Start Ingestors
    # Kafka
    kafka_server = "localhost:9092"
    kafka_monitor = EnterpriseKafkaMonitor(
        kafka_server, ["enterprise-logs"], log_queue, loop
    )
    kafka_monitor.start()

    # Local File Monitor
    log_paths = config.get("sources", {}).get("logs", [])
    if log_paths:
        file_monitor = LogMonitor(log_paths, log_queue, loop)
        file_monitor.start()

    # Webhook
    webhook_port = config.get("sources", {}).get("webhook_port", 8080)
    webhook_ingestor = WebhookIngestor(
        port=webhook_port, processing_queue=log_queue, loop=loop
    )
    webhook_ingestor.start()

    # Wi-Fi Packet Sniffer
    wifi_interface = config.get("sources", {}).get("wifi_interface", "lo")
    if wifi_interface:
        wifi_monitor = NetworkPacketMonitor(
            interface=wifi_interface, processing_queue=log_queue, loop=loop
        )
        wifi_monitor.start()

    # 2a. Deception Engine
    deception_engine = CyberDeception(config, log_queue, loop)
    deception_engine.start()
    print(
        f"{Colors.OKGREEN}[+] Infrastructure: Cyber Deception Engine Active (Ghost Nodes Deployed){Colors.ENDC}"
    )

    # 2b. Optional Threat Simulator (Mode 2: WarGames)
    if mode == "2" or config.get("simulation", {}).get("enabled", False):
        log_path = log_paths[0] if log_paths else "test_log.txt"
        simulator = ThreatSimulator(log_file=log_path)
        simulator.start()
        print(
            f"{Colors.OKGREEN}[+] Simulation: Autonomous Threat Injector Active{Colors.ENDC}"
        )
        print(
            f"    🎯 Mode     : Continuous Attack Injection (File & Kafka)", flush=True
        )

    # 3. Intelligence
    analyzer = Analyzer(config)

    print(
        f"\n{Colors.OKBLUE}=================================================================={Colors.ENDC}"
    )
    print(f"{Colors.BOLD}[✓] C.O.R.E IS ONLINE & MONITORING TRAFFIC{Colors.ENDC}")
    print(
        f"{Colors.OKBLUE}=================================================================={Colors.ENDC}\n"
    )

    # Start Maintenance Task
    asyncio.create_task(run_maintenance(db))

    # 4. Main AI Loop
    while True:
        log_entry = await log_queue.get()
        if log_entry:
            result = await analyzer.analyze_log(log_entry)
            risk = result.get("risk_score", 0)
            if risk >= 50:
                color = Colors.FAIL if risk >= 90 else Colors.WARNING
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(
                    f"{color}[{timestamp}] 🚨 THREAT DETECTED (Risk: {risk}/100){Colors.ENDC}",
                    flush=True,
                )
                print(f"    🔎 Analysis : {result['analysis']}", flush=True)
                print(f"    📦 Source   : {result['source']}", flush=True)

                threshold = config.get("response", {}).get("block_threshold", 90)
                if risk >= threshold:
                    ip = firewall.extract_ip(result["raw_content"])
                    if ip:
                        print(
                            f"    🛡️  Defense  : Automatically blocking {ip}...",
                            flush=True,
                        )
                        firewall.block_ip(ip, reason=result["analysis"])
                        await remote_responder.execute_action(
                            "REMOTELY_BLOCK_IP", ip, reason=result["analysis"]
                        )
                print("", flush=True)
            db.save_alert(result)
        log_queue.task_done()


def launch_dashboard():
    """Starts the streamlit dashboard as a silent background process."""
    print(
        f"  {Colors.OKGREEN}>>{Colors.ENDC} Syncing Mission Control UI (Port 8501)..."
    )

    # Verify file exists
    dash_path = "interface/dashboard.py"
    if not os.path.exists(dash_path):
        print(f"  {Colors.FAIL}[!] Critical: {dash_path} not found.{Colors.ENDC}")
        return

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    # We use a log file to catch early startup errors if it fails
    with open("logs/dashboard_startup.log", "w") as f_log:
        p = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                dash_path,
                "--server.port",
                "8501",
                "--server.address",
                "0.0.0.0",
            ],
            stdout=f_log,
            stderr=subprocess.STDOUT,
            env=env,
        )
    background_subprocesses.append(p)


def main():
    print_banner()
    print_capabilities()

    print(f"\n{Colors.WARNING}SYSTEM DEPLOYMENT MODES:{Colors.ENDC}")
    print(f"  [1] {Colors.OKCYAN}🚀 MISSION READY{Colors.ENDC}   (Core + Dashboard)")
    print(
        f"  [2] {Colors.FAIL}⚔️  WARGAMES{Colors.ENDC}       (Core + Dashboard + integrated Sim)"
    )
    print(f"  [3] {Colors.OKGREEN}🧠 HEADLESS{Colors.ENDC}       (Core Only)")
    print(f"  [4] {Colors.FAIL}❌ ABORT{Colors.ENDC}")

    choice = input(f"\n{Colors.BOLD}COMMAND -> {Colors.ENDC}")

    if choice == "4":
        print(f"{Colors.OKBLUE}[*] Mission Aborted. Stand-down complete.{Colors.ENDC}")
        return

    # Load Config
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)

    if choice in ["1", "2"]:
        launch_dashboard()
        time.sleep(2)
        print(
            f"\n{Colors.OKCYAN}[✓] Dashboard active at http://localhost:8501{Colors.ENDC}"
        )

    # Core engine runs as the main async entry point
    try:
        asyncio.run(core_engine(choice, config))
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}[!] INITIATING SYSTEM TEARDOWN...{Colors.ENDC}")
        for p in background_subprocesses:
            p.terminate()
            try:
                p.wait(timeout=2)
            except:
                p.kill()
        print(
            f"{Colors.OKGREEN}[✓] Teardown complete. All nodes successfully disengaged.{Colors.ENDC}\n"
        )


if __name__ == "__main__":
    main()
