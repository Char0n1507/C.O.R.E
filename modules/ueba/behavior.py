import time
import re

class BehaviorAnalyzer:
    """
    User & Entity Behavior Analytics (UEBA).
    Tracks state across multiple log events to detect patterns like Brute Force 
    that a single-line rule engine would miss.
    """
    def __init__(self, time_window=60, threshold=5):
        self.time_window = time_window
        self.threshold = threshold
        self.failed_logins = {}  # Format: {"ip": [timestamp1, timestamp2, ...]}

    def analyze(self, log_entry):
        content = log_entry.get("content", "").lower()
        
        # We only care about failed connections for this behavior model
        if "failed password" not in content and "authentication failure" not in content:
            return None

        # Extract IP
        ip_pattern = r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
        match = re.search(ip_pattern, content)
        if not match:
            return None
        
        ip = match.group(1)
        current_time = time.time()
        
        if ip not in self.failed_logins:
            self.failed_logins[ip] = []
        
        # Prune old events outside the time window
        self.failed_logins[ip] = [ts for ts in self.failed_logins[ip] if current_time - ts <= self.time_window]
        
        # Add new event
        self.failed_logins[ip].append(current_time)
        
        # Check threshold
        if len(self.failed_logins[ip]) >= self.threshold:
            # Clear the record so we don't spam duplicate alerts for the exact same burst
            self.failed_logins[ip] = []
            return {
                "risk_score": 95,
                "analysis": "UEBA: Contextual Brute Force Detected (>5 failures in 60s)",
                "action": "Block IP Automatically"
            }

        return None
