import requests
import logging
import os
import base64

class VirusTotalEnricher:
    """Queries the VirusTotal API to check IP reputation."""
    
    def __init__(self):
        self.api_key = os.getenv("VIRUSTOTAL_API_KEY")
        self.base_url = "https://www.virustotal.com/api/v3/ip_addresses"
        self.cache = {} # Cache responses to save API quota

    def check_ip(self, ip_address):
        """
        Queries VT for the given IP. Returns a dict with risk score.
        If the IP is malicious engines >= 3, it's flagged as high risk.
        """
        if not ip_address or not self.api_key:
            return None
            
        # Don't query private or loopback IPs
        if ip_address.startswith("127.") or ip_address.startswith("192.168.") or ip_address.startswith("10."):
            return None
            
        if ip_address in self.cache:
            return self.cache[ip_address]

        headers = {
            "accept": "application/json",
            "x-apikey": self.api_key
        }

        try:
            logging.debug(f"[*] Querying VirusTotal for {ip_address}")
            response = requests.get(f"{self.base_url}/{ip_address}", headers=headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                stats = data["data"]["attributes"]["last_analysis_stats"]
                
                malicious = stats.get("malicious", 0)
                suspicious = stats.get("suspicious", 0)
                
                # Rule of thumb: if 3 or more engines say it's malicious, it's very bad.
                is_malicious = malicious >= 3
                
                result = {
                    "malicious_votes": malicious,
                    "suspicious_votes": suspicious,
                    "is_malicious": is_malicious,
                    "summary": f"Known Malicious IP! Flagged by {malicious} security engines on VirusTotal." if is_malicious else "Clean/Unknown on VirusTotal"
                }
                
                self.cache[ip_address] = result
                return result
            else:
                logging.debug(f"[!] VirusTotal API Error: {response.status_code}")
                return None
                
        except Exception as e:
            logging.debug(f"[!] VirusTotal Request Failed: {e}")
            return None

    def check_url(self, url):
        """
        Queries VT for the given URL. Returns a dict with risk score.
        If the URL is malicious engines >= 3, it's flagged as high risk.
        """
        if not url or not self.api_key:
            return None
            
        if url in self.cache:
            return self.cache[url]

        headers = {
            "accept": "application/json",
            "x-apikey": self.api_key
        }

        try:
            logging.debug(f"[*] Querying VirusTotal for URL: {url}")
            # VT API v3 requires URL identifiers to be base64 url-safe without padding
            url_id = base64.urlsafe_b64encode(url.encode()).decode().strip("=")
            response = requests.get(f"https://www.virustotal.com/api/v3/urls/{url_id}", headers=headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                stats = data["data"]["attributes"]["last_analysis_stats"]
                
                malicious = stats.get("malicious", 0)
                suspicious = stats.get("suspicious", 0)
                
                is_malicious = malicious >= 3
                
                result = {
                    "malicious_votes": malicious,
                    "suspicious_votes": suspicious,
                    "is_malicious": is_malicious,
                    "summary": f"Known Malicious URL! Flagged by {malicious} security engines on VirusTotal." if is_malicious else "Clean/Unknown URL on VirusTotal"
                }
                
                self.cache[url] = result
                return result
            else:
                logging.debug(f"[!] VirusTotal API Error: {response.status_code}")
                return None
                
        except Exception as e:
            logging.debug(f"[!] VirusTotal URL Request Failed: {e}")
            return None
