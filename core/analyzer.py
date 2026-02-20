import os
import json
import asyncio
import requests
import google.generativeai as genai
from google.api_core import exceptions
from modules.ueba.behavior import BehaviorAnalyzer
from modules.enrichment.geo import GeoEnricher
from modules.enrichment.virustotal import VirusTotalEnricher
import re

class Analyzer:
    def __init__(self, use_llm=True, provider="gemini", ollama_url="http://localhost:11434", ollama_model="llama3"):
        self.use_llm = use_llm
        self.provider = provider
        self.ollama_url = ollama_url
        self.ollama_model = ollama_model
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.model = None
        self.ueba = BehaviorAnalyzer(time_window=60, threshold=5)
        self.geo = GeoEnricher()
        self.vt = VirusTotalEnricher()
        
        if self.use_llm:
            if self.provider == "gemini" and self.api_key:
                print("[*] Configuring Gemini Pro for Analysis...")
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-pro')
            elif self.provider == "ollama":
                print(f"[*] Configuring Local Ollama LLM ({self.ollama_model}) at {self.ollama_url}...")
            else:
                self.use_llm = False
        else:
            self.use_llm = False

    async def analyze_log(self, log_entry):
        """
        Analyzes a log entry. Uses basic rules for speed, and escalates to Gemini
        if the log looks suspicious or interesting.
        """
        content = log_entry.get("content", "").lower()
        
        # Extract IP for Enrichment
        ip = None
        match = re.search(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", content)
        if match:
            ip = match.group(1)
            
        # Enrich Location Map
        loc = self.geo.get_location(ip) if ip else {"country": "Unknown", "city": "Unknown", "lat": 0.0, "lon": 0.0, "alpha_3": "USA"}

        # Base Analysis Dictionary
        base_result = {
            "timestamp": log_entry.get("timestamp"),
            "source": log_entry.get("source"),
            "raw_content": log_entry.get("content"),
            "country": loc["country"],
            "city": loc["city"],
            "lat": loc["lat"],
            "lon": loc["lon"],
            "alpha_3": loc["alpha_3"],
            "ip": ip
        }

        # 0. VirusTotal Threat Intel (Fastest, High-Confidence)
        vt_data = self.vt.check_ip(ip) if ip else None
        if vt_data and vt_data.get("is_malicious"):
            result = base_result.copy()
            result.update({
                "risk_score": 100,
                "analysis": vt_data["summary"],
                "action": "Block IP (VirusTotal Intel)"
            })
            return result

        # 1. Fast Pre-Filter (Don't waste LLM calls on noise)
        suspicious_keywords = [
            "failed", "error", "denied", "segfault", "panic", "root", "admin",
            "unauthorized", "refused", "attack", "malware", "virus", "trojan",
            "tripwire", "honeypot"
        ]
        
        is_suspicious = any(kw in content for kw in suspicious_keywords)
        
        if not is_suspicious:
            result = base_result.copy()
            result.update({
                "risk_score": 0,
                "analysis": "Routine Log",
                "action": "Monitor"
            })
            return result

        # 2. Deep Analysis (Gemini / Ollama)
        if self.use_llm:
            try:
                # We offload the blocking API call to a thread
                response = await asyncio.to_thread(self._query_llm, log_entry['content'])
                result = base_result.copy()
                result.update({
                    "risk_score": response.get("risk_score", 50),
                    "analysis": response.get("summary", "AI Analysis Failed"),
                    "action": response.get("action", "Monitor")
                })
                return result
            except Exception as e:
                print(f"[!] Gemini Analysis Error: {e}")
                # Fallback to rules

        # Check UEBA Stateful Analysis First (for behaviors across multiple logs)
        ueba_result = self.ueba.analyze(log_entry)
        if ueba_result:
            result = base_result.copy()
            result.update({
                "risk_score": ueba_result["risk_score"],
                "analysis": ueba_result["analysis"],
                "action": ueba_result["action"]
            })
            return result

        # 3. Rule-Based Fallback (Single Line Analysis)
        risk_score = 50
        analysis = "Suspicious Activity Detected (Rule-Based)"
        
        if "honeypot" in content or "tripwire" in content:
            risk_score = 100
            analysis = "Honeypot Triggered (Critical Action Required)"
        elif "failed password" in content or "authentication failure" in content:
            # We don't alert on single failure anymore, we rely on the UEBA module!
            risk_score = 20  
            analysis = "Single Failed Login (Monitoring)"
        elif "root" in content:
            risk_score = 80
            analysis = "Privileged Access Attempt"

        result = base_result.copy()
        result.update({
            "risk_score": risk_score,
            "analysis": analysis,
            "action": "Monitor"
        })
        return result

    def _query_llm(self, log_line):
        """Queries the configured LLM (Gemini or Ollama). Returns a dict."""
        prompt = f"""
        You are an expert Security Operations Center (SOC) Analyst.
        Analyze the following system log entry for security threats.
        
        Log: "{log_line}"
        
        Format your response as a valid JSON object with these keys:
        - risk_score (integer 0-100)
        - summary (short explanation of the event)
        - action (recommended action like 'Block IP', 'Isolate Host', 'Identify User', 'Ignore')
        
        Do not include markdown formatting or extra text. Just the JSON.
        """
        try:
            if self.provider == "gemini":
                response = self.model.generate_content(prompt)
                text = response.text.strip()
            elif self.provider == "ollama":
                headers = {'Content-Type': 'application/json'}
                data = {
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                }
                resp = requests.post(f"{self.ollama_url}/api/generate", headers=headers, json=data, timeout=30)
                resp.raise_for_status()
                text = resp.json().get("response", "").strip()
            else:
                raise ValueError("Unknown LLM Provider configured.")

            # Clean up markdown if AI adds it
            if text.startswith("```json"):
                text = text[7:-3]
            elif text.startswith("```"):
                text = text[3:-3]
            return json.loads(text)
        except Exception as e:
            print(f"[!] LLM Analysis Error: {e}")
            return {"risk_score": 50, "summary": "AI Parsing Error", "action": "Manual Review"}
