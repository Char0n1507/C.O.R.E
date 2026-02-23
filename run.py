import subprocess
import sys
import time
import os
import signal

class Colors:
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_banner():
    banner = f"""{Colors.OKCYAN}
   ____   ___  ____  _____ 
  / ___| / _ \|  _ \| ____|
 | |    | | | | |_) |  _|  
 | |___ | |_| |  _ <| |___ 
  \\____| \\___/|_| \\_\\_____|
                           
  MASTER LAUNCHER ACTIVE
  ------------------------------------------------{Colors.ENDC}"""
    print(banner)

def main():
    print_banner()
    print(f"{Colors.BOLD}[*] Initializing C.O.R.E. AI SOC Ecosystem...{Colors.ENDC}\n")
    
    processes = []
    
    # Path configurations
    python_exe = sys.executable
    main_script = "main.py"
    dashboard_script = os.path.join("interface", "dashboard.py")
    adversary_script = os.path.join("modules", "agents", "adversary.py")

    try:
        # Display Feature Set
        print(f"{Colors.BOLD}{Colors.OKCYAN}C.O.R.E. Ecosystem Architecture & Capabilities:{Colors.ENDC}")
        features = [
            ("🧠 AI Analyst Engine", "Ingests and analyzes logs/telemetry dynamically via LLMs (Gemini/Ollama)"),
            ("🛡️ Autonomous Response", "Automatically drops IP packets using iptables or remote Wazuh APIs"),
            ("🕸️ Cyber Deception", "Spins up Honeypots (Ghost Nodes) that trap internal network scanners"),
            ("📊 Mission Control UI", "A unified dashboard (Streamlit) for real-time visualization and neural queries"),
            ("📄 Executive Reporting", "Generates PDF Board-Level Briefs mapping threats to MITRE ATT&CK"),
            ("🕵️‍♂️ Red Team Adversary", "An optional autonomous agent that tests defenses using 0-day techniques"),
        ]
        
        for name, desc in features:
            print(f"  {Colors.OKGREEN}[+]{Colors.ENDC} {Colors.BOLD}{name:<25}{Colors.ENDC} - {desc}")
        print("\n")

        # Prompt for enterprise mode feature
        enable_rt = input(f"{Colors.BOLD}{Colors.WARNING}[?] Do you want to enable the Autonomous Red Team Adversary? (y/N): {Colors.ENDC}").strip().lower()
        if enable_rt in ['y', 'yes', 'true']:
            run_adversary = True
            print(f"{Colors.OKCYAN}[*] Red Team Agent Scheduled for Deployment.{Colors.ENDC}\n")
        else:
            run_adversary = False
            print(f"[*] Red Team Agent \033[91mDeactivated\033[0m. Operating in standard defense mode.\n")

        # 1. Launch Core Engine
        print(f"{Colors.OKGREEN}[+] Starting Core Command Center (main.py)...{Colors.ENDC}")
        p_main = subprocess.Popen([python_exe, main_script])
        processes.append(p_main)
        time.sleep(3) # Give it time to initialize DB and queues
        
        # 2. Launch Streamlit Dashboard
        print(f"{Colors.OKGREEN}[+] Starting Mission Control (dashboard.py)...{Colors.ENDC}")
        # Use python -m streamlit to ensure it uses the venv streamlit
        p_dash = subprocess.Popen(
            [python_exe, "-m", "streamlit", "run", dashboard_script, "--server.port", "8501", "--server.address", "0.0.0.0"],
            stdout=subprocess.DEVNULL, # Hide verbose streamlit startup logs to keep console clean
            stderr=subprocess.DEVNULL
        )
        processes.append(p_dash)
        time.sleep(2)
        
        # 3. Launch Red Team Adversary (Conditional)
        if run_adversary:
            print(f"{Colors.OKGREEN}[+] Starting Autonomous Red Team Agent (adversary.py)...{Colors.ENDC}")
            p_agent = subprocess.Popen([python_exe, adversary_script])
            processes.append(p_agent)
        
        print(f"\n{Colors.BOLD}{Colors.OKCYAN}[✓] ALL SYSTEMS GREEN. Ecosystem is running.{Colors.ENDC}")
        print(f"    - Dashboard URL: http://localhost:8501")
        print(f"    - Press Ctrl+C at any time to gracefully shut down all components.\n")
        
        # Keep the master process alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}=================================================================={Colors.ENDC}")
        print(f"{Colors.WARNING}[!] Shutting down all C.O.R.E. components...{Colors.ENDC}")
        
        # Gracefully terminate all child processes
        for p in processes:
            p.terminate()
            
        # Wait for them to close
        for p in processes:
            p.wait()
            
        print(f"{Colors.OKGREEN}[✓] Teardown complete. Goodbye.{Colors.ENDC}")

if __name__ == "__main__":
    main()
