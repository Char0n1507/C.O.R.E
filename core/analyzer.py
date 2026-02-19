import os
import json
import asyncio
import google.generativeai as genai
from google.api_core import exceptions
from modules.ueba.behavior import BehaviorAnalyzer
from modules.enrichment.geo import GeoEnricher
import re

class Analyzer:
    def __init__(self, use_llm=True):
        self.use_llm = use_llm
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.model = None
        self.ueba = BehaviorAnalyzer(time_window=60, threshold=5)
        self.geo = GeoEnricher()
        
        if self.use_llm and self.api_key:
            print("[*] Configuring Gemini Pro for Analysis...")
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-pro')
        else:
            print("[!] No GOOGLE_API_KEY found or LLM disabled. Using basic rules.")
            self.use_llm = False

    async def analyze_log(self, log_entry):
        """
        Analyzes a log entry. Uses basic rules for speed, and escalates to Gemini
        if the log looks suspicious or interesting.
        """
        content = log_entry.get("content", "").lower()
        
        # 1. Fast Pre-Filter (Don't waste LLM calls on noise)
        suspicious_keywords = [
            "failed", "error", "denied", "segfault", "panic", "root", "admin",
            "unauthorized", "refused", "attack", "malware", "virus", "trojan",
            "tripwire", "honeypot"
        ]
        
        is_suspicious = any(kw in content for kw in suspicious_keywords)
        
        if not is_suspicious:
            return {
                "timestamp": log_entry.get("timestamp"),
                "source": log_entry.get("source"),
                "raw_content": log_entry.get("content"),
                "risk_score": 0,
                "analysis": "Routine Log"
            }

        # 2. Deep Analysis (Gemini)
        if self.use_llm:
            try:
                # We offload the blocking API call to a thread
                response = await asyncio.to_thread(self._query_gemini, log_entry['content'])
                return {
                    "timestamp": log_entry.get("timestamp"),
                    "source": log_entry.get("source"),
                    "raw_content": log_entry.get("content"),
                    "risk_score": response.get("risk_score", 50),
                    "analysis": response.get("summary", "AI Analysis Failed"),
                    "action": response.get("action", "Monitor")
                }
            except Exception as e:
                print(f"[!] Gemini Analysis Error: {e}")
                # Fallback to rules

        # Check UEBA Stateful Analysis First (for behaviors across multiple logs)
        ueba_result = self.ueba.analyze(log_entry)
        if ueba_result:
            return {
                "timestamp": log_entry.get("timestamp"),
                "source": log_entry.get("source"),
                "raw_content": log_entry.get("content"),
                "risk_score": ueba_result["risk_score"],
                "analysis": ueba_result["analysis"],
                "action": ueba_result["action"]
            }

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

        # Extract IP for GeoEnrichment
        ip = None
        match = re.search(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", content)
        if match:
            ip = match.group(1)
            
        # Enrich Location Map
        loc = self.geo.get_location(ip) if ip else {"country": "Unknown", "city": "Unknown", "lat": 0.0, "lon": 0.0, "alpha_3": "USA"}

        return {
            "timestamp": log_entry.get("timestamp"),
            "source": log_entry.get("source"),
            "raw_content": log_entry.get("content"),
            "risk_score": risk_score,
            "analysis": analysis,
            "action": "Monitor",
            "country": loc["country"],
            "city": loc["city"],
            "lat": loc["lat"],
            "lon": loc["lon"],
            "alpha_3": loc["alpha_3"],
            "ip": ip
        }

    def _query_gemini(self, log_line):
        """Queries Gemini Pro. Returns a dict."""
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
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            # Clean up markdown if Gemini adds it
            if text.startswith("```json"):
                text = text[7:-3]
            return json.loads(text)
        except Exception:
            return {"risk_score": 50, "summary": "AI Parsing Error", "action": "Manual Review"}
