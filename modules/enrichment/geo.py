import pycountry
from ip2geotools.databases.noncommercial import DbIpCity
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
            # Use free DbIpCity database
            response = DbIpCity.get(ip_address, api_key='free')
            
            # Convert 2-letter country code to 3-letter for Plotly maps
            try:
                country_obj = pycountry.countries.get(alpha_2=response.country)
                alpha_3 = country_obj.alpha_3 if country_obj else "USA"
            except:
                alpha_3 = "USA"

            data = {
                "country": response.country,
                "city": response.city,
                "lat": response.latitude,
                "lon": response.longitude,
                "alpha_3": alpha_3
            }
            self.cache[ip_address] = data
            return data
            
        except Exception as e:
            # Fallback to unknown if API fails or IP is private network
            logging.debug(f"GeoIP Lookup failed for {ip_address}: {e}")
            self.cache[ip_address] = {"country": "Unknown", "city": "Unknown", "lat": 0.0, "lon": 0.0, "alpha_3": "USA"}
            return self.cache[ip_address]
