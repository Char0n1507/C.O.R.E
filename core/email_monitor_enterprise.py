import asyncio
import time
import requests
import msal

class EnterpriseEmailMonitor:
    def __init__(self, config, processing_queue, loop):
        self.config = config
        self.processing_queue = processing_queue
        self.loop = loop
        
        self.tenant_id = self.config.get('tenant_id')
        self.client_id = self.config.get('client_id')
        self.client_secret = self.config.get('client_secret')
        self.user_id = self.config.get('user_id') # email to monitor
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        
        self.running = False
        
        self.app = msal.ConfidentialClientApplication(
            self.client_id, authority=self.authority,
            client_credential=self.client_secret,
        )
        
    def _acquire_token(self):
        result = self.app.acquire_token_silent(["https://graph.microsoft.com/.default"], account=None)
        if not result:
            result = self.app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
        if "access_token" in result:
            return result["access_token"]
        else:
            raise Exception(f"Failed to acquire MS Graph token: {result.get('error_description')}")

    def start(self):
        if not all([self.tenant_id, self.client_id, self.client_secret, self.user_id]):
            print("[!] Skipping Enterprise Email Monitor (Missing MS Graph Credentials)")
            return
            
        print(f"[*] Starting Enterprise MS Graph Email Monitor for: {self.user_id}")
        self.running = True
        self.task = asyncio.create_task(self._poll_graph_api())

    async def _poll_graph_api(self):
        last_check_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() - 3600)) # last 1 hr
        
        while self.running:
            try:
                # Use thread to prevent blocking asyncio loop during network call
                await asyncio.to_thread(self._check_inbox, last_check_time)
                last_check_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            except Exception as e:
                print(f"[!] MS Graph API Error: {e}")
                
            await asyncio.sleep(60) # check every minute

    def _check_inbox(self, last_check_time):
        token = self._acquire_token()
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        
        # OData query to get messages received after last_check_time
        endpoint = f"https://graph.microsoft.com/v1.0/users/{self.user_id}/messages?$filter=receivedDateTime ge {last_check_time}&$select=subject,from,bodyPreview,body"
        
        response = requests.get(endpoint, headers=headers)
        response.raise_for_status()
        
        messages = response.json().get('value', [])
        
        for msg in messages:
            subject = msg.get('subject', 'No Subject')
            sender_address = msg.get('from', {}).get('emailAddress', {}).get('address', 'Unknown')
            body = msg.get('bodyPreview', '')
            
            content_str = f"EMAIL PARSED: Subject: {subject} | From: {sender_address} | Body: {body}"
            
            email_data = {
                "subject": subject,
                "from": sender_address,
                "body": body,
                "raw_headers": {} # O365 Graph abstracts headers slightly differently
            }
            
            print(f"[*] Enterprise EmailMonitor Ingested: {subject} from {sender_address}")
            
            asyncio.run_coroutine_threadsafe(
                self.processing_queue.put({
                    "source": f"oauth2://msgraph/{self.user_id}",
                    "content": content_str,
                    "timestamp": time.time(),
                    "type": "email",
                    "email_data": email_data
                }),
                self.loop
            )

    def stop(self):
        self.running = False
        print("[*] Enterprise Email Monitor stopped.")
