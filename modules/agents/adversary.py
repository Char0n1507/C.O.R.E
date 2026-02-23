import os
import sys
import yaml
import time
import random
import requests
import json

# Path Setup
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(PROJECT_ROOT)

class RedTeamAgent:
    def __init__(self):
        print("[\033[91m💀\033[0m] Initializing Autonomous Red Team Agent...")
        self.config = self._load_config()
        self.provider = self.config.get("analyzer", {}).get("provider", "ollama")
        if self.provider == "rules":
            self.provider = "ollama"
        self.ollama_url = self.config.get("analyzer", {}).get("ollama_url", "http://localhost:11434")
        self.ollama_model = self.config.get("analyzer", {}).get("ollama_model", "llama3")
        self.api_key = os.getenv("GOOGLE_API_KEY")
        
        # The agent can sneak a peek at what C.O.R.E. successfully blocked!
        from core.database_enterprise import EnterpriseDatabase
        self.db = EnterpriseDatabase()
        
        self.log_file = os.path.join(PROJECT_ROOT, "test_log.txt")

    def _load_config(self):
        config_path = os.path.join(PROJECT_ROOT, "config.yaml")
        try:
            with open(config_path, "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            return {}

    def get_context(self):
        # The agent checks if its last attacks were blocked
        try:
            alerts = self.db.get_recent_alerts(limit=5)
            if alerts:
                last_defense = []
                for a in alerts:
                    last_defense.append(f"- Blocked IP {a.get('ip', 'Unknown')} because '{a.get('analysis', 'Unknown')}'")
                return "\n".join(last_defense)
        except:
            pass
        return "No recent defenses observed."

    def generate_payload(self):
        defense_context = self.get_context()
        
        prompt = f"""
        You are an autonomous Red Team AI Adversary. Your goal is to bypass a Security Operations Center (SOC) agent.
        The SOC Agent's recent defensive actions are:
        {defense_context}
        
        Your task is to generate a SINGLE line of a raw Linux or Web Server log representing a new, stealthy cyber attack.
        Do NOT repeat techniques that were just blocked. If brute force was blocked, try SQL injection, XSS, Path Traversal, LFI, Command Injection, or polymorphic variations.
        Make it look extremely realistic. Use varied IP addresses (e.g., 10.x.x.x or random public IPs).
        
        Format your response as a valid JSON object with these keys:
        - log_line (the raw single string of the fake server log)
        - intent (what you are trying to achieve)
        - evasion_tactic (how this is supposed to bypass the SOC)
        
        Do not include markdown formatting. Just the JSON.
        """
        
        try:
            if self.provider == "ollama":
                req_data = {
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                }
                resp = requests.post(f"{self.ollama_url}/api/generate", json=req_data, timeout=120)
                if resp.status_code == 200:
                    text = resp.json().get("response", "").strip()
                else:
                    return None
            elif self.provider == "gemini":
                import google.generativeai as genai
                if not self.api_key: return None
                genai.configure(api_key=self.api_key)
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(prompt)
                text = response.text.strip()
                if text.startswith("```json"):
                    text = text[7:-3]
                elif text.startswith("```"):
                    text = text[3:-3]
            else:
                return None
            
            # Simple fix for LLM outputting backticks anyway
            if text.startswith("```json"):
                text = text[7:-3]
            elif text.startswith("```"):
                text = text[3:-3]
                
            return json.loads(text)
        except Exception as e:
            print(f"[!] Red Team LLM Error: {e}")
            return None

    def run(self):
        print("[\033[91m💀\033[0m] Red Team Agent is now actively targeting the C.O.R.E ecosystem (Press Ctrl+C to stop).")
        while True:
            print("\n[\033[91m💀\033[0m] Analyzing defenses and plotting next attack...")
            attack_data = self.generate_payload()
            
            if attack_data and "log_line" in attack_data:
                log_line = attack_data["log_line"]
                
                # Ensure the fake log has a timestamp
                timestamp = time.strftime("%b %d %H:%M:%S")
                host = "ubuntu-server"
                if not timestamp[:6] in log_line:
                    log_line = f"{timestamp} {host} {log_line}"
                    
                print(f"    🎯 \033[1mIntent:\033[0m  {attack_data.get('intent', 'Unknown')}")
                print(f"    🥷  \033[1mEvasion:\033[0m {attack_data.get('evasion_tactic', 'Unknown')}")
                print(f"    \033[91m->\033[0m Payload: {log_line}")
                
                with open(self.log_file, "a") as f:
                    f.write(log_line + "\n")
                    f.flush()
            else:
                print("    [!] Failed to compile payload. Retrying...")
            
            # Wait before the next strike (stealthy mode)
            delay = random.uniform(5.0, 15.0)
            print(f"[⏳] Hibernating for {delay:.1f} seconds to blend in with background noise...")
            time.sleep(delay)

if __name__ == "__main__":
    agent = RedTeamAgent()
    try:
        agent.run()
    except KeyboardInterrupt:
        print("\n[\033[91m💀\033[0m] Red Team Agent disengaging.")
