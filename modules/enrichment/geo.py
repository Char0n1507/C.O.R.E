import pycountry
import requests
import logging

class GeoEnricher:
    """Enriches IP addresses with geographical data."""
    def __init__(self):
        self.cache = {
            # Pre-cache test loopback IPs so we don't spam free APIs
            "127.0.0.1": {"country": "Local", "city": "Localhost", "lat": 0.0, "lon": 0.0, "alpha_3": "USA"}
        }

    def get_location(self, ip_address):
        if not ip_address:
            return None
            
        if ip_address in self.cache:
            return self.cache[ip_address]
            
        try:
            # Use free ip-api.com endpoint
            response = requests.get(f"http://ip-api.com/json/{ip_address}", timeout=5).json()
            
            if response.get("status") == "fail":
                raise Exception(response.get("message", "ip-api failed"))
                
            country_name = response.get("country", "Unknown")
            country_code = response.get("countryCode", "")
            city = response.get("city", "Unknown")
            lat = response.get("lat", 0.0)
            lon = response.get("lon", 0.0)
            
            # Convert 2-letter country code to 3-letter for Plotly maps
            try:
                country_obj = pycountry.countries.get(alpha_2=country_code)
                alpha_3 = country_obj.alpha_3 if country_obj else ""
            except:
                alpha_3 = ""

            data = {
                "country": country_name if country_name != "Unknown" else "Internal/Local",
                "city": city,
                "lat": lat,
                "lon": lon,
                "alpha_3": alpha_3
            }
            self.cache[ip_address] = data
            return data
            
        except Exception as e:
            # Fallback for internal/private IPs or API failures
            self.cache[ip_address] = {"country": "Internal/Private", "city": "N/A", "lat": 0.0, "lon": 0.0, "alpha_3": ""}
            return self.cache[ip_address]
