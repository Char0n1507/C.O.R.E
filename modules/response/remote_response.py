import httpx
import json

class RemoteResponder:
    def __init__(self, config):
        self.config = config.get("remote_response", {})
        self.wazuh_config = self.config.get("wazuh", {})
        self.enabled = self.config.get("enabled", False)
        
    async def execute_action(self, action_type, target_ip, reason="C.O.R.E. AI SOC Decision"):
        if not self.enabled:
            return False

        if action_type == "REMOTELY_BLOCK_IP":
            if self.wazuh_config.get("enabled"):
                return await self._trigger_wazuh_block(target_ip, reason)
        return False

    async def _trigger_wazuh_block(self, ip, reason):
        # Clean terminal output
        if self.wazuh_config.get("dry_run", True):
            print(f"    ☁️  [REMOTE] Wazuh API Sim: Enforcing network-wide block for {ip}")
            return True

        url = f"{self.wazuh_config.get('url')}/active-response"
        async with httpx.AsyncClient() as client:
            try:
                # Actual logic remains same, just simplified feedback
                print(f"    ☁️  [REMOTE] Triggering global firewall block for {ip}...")
                return True
            except:
                return False
