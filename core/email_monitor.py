import asyncio
import time
import os
from imapclient import IMAPClient
import mailparser

class EmailMonitor:
    def __init__(self, config, processing_queue, loop):
        self.config = config
        self.processing_queue = processing_queue
        self.loop = loop
        self.server = self.config.get('server')
        self.username = self.config.get('username')
        self.password = self.config.get('password')
        self.folder = self.config.get('folder', 'INBOX')
        self.enabled = self.config.get('enabled', False)
        self.running = False
        
    async def run(self):
        if not self.enabled or not self.server:
            return
            
        print(f"[*] Starting Email Monitor for {self.username} on {self.server}...")
        self.running = True
        
        # If it's the demo server, run a local file poll instead
        if self.server == "imap.example.com":
            print("[*] Email Monitor running in DEMO mode reading from test_emails.jsonl")
            await self._run_demo()
            return
            
        while self.running:
            try:
                # Use to_thread to prevent blocking the asyncio loop
                await asyncio.to_thread(self._check_email)
            except Exception as e:
                # This may routinely fail if the provided config credentials are fake
                print(f"[!] Email Monitor Error (Check IMAP Credentials): {e}")
                
            # If we fail, or succeed, wait a bit before checking again
            await asyncio.sleep(30)

    async def _run_demo(self):
        """Monitors a local file for new JSONL emails since IMAP is disabled"""
        filepath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "test_emails.jsonl")
        
        # Create file if it doesn't exist
        if not os.path.exists(filepath):
            with open(filepath, 'w') as f:
                pass
                
        with open(filepath, 'r') as f:
            f.seek(0, os.SEEK_END)
            
            while self.running:
                line = f.readline()
                if not line:
                    await asyncio.sleep(1)
                    continue
                    
                line = line.strip()
                if not line:
                    continue
                    
                import json
                try:
                    data = json.loads(line)
                    sender = data.get("from", "Unknown")
                    subject = data.get("subject", "No Subject")
                    body = data.get("body", "")
                    
                    content_str = f"EMAIL PARSED: Subject: {subject} | From: {sender} | Body: {body}"
                    
                    email_data = {
                        "subject": subject,
                        "from": sender,
                        "body": body,
                        "raw_headers": data.get("headers", {})
                    }
                    
                    print(f"[*] EmailMonitor (Demo) Ingested: {subject} from {sender}")
                    
                    await self.processing_queue.put({
                        "source": f"imap://{self.username}@{self.server}",
                        "content": content_str,
                        "timestamp": time.time(),
                        "type": "email",
                        "email_data": email_data
                    })
                except Exception as e:
                    print(f"[!] Failed to parse test jsonl email: {e}")
            
    def _check_email(self):
        try:
            with IMAPClient(self.server, timeout=10) as client:
                client.login(self.username, self.password)
                client.select_folder(self.folder)
                
                # Search for UNSEEN messages
                messages = client.search('UNSEEN')
                if not messages:
                    return
                    
                response = client.fetch(messages, ['RFC822'])
                for msg_id, data in response.items():
                    parsed_mail = mailparser.parse_from_bytes(data[b'RFC822'])
                    
                    sender = ", ".join([f"{e[0]} <{e[1]}>" if e[0] else e[1] for e in parsed_mail.from_]) if hasattr(parsed_mail, 'from_') else "Unknown"
                    subject = parsed_mail.subject
                    body = parsed_mail.text_plain[0] if parsed_mail.text_plain else (parsed_mail.text_html[0] if parsed_mail.text_html else "")
                    
                    content_str = f"EMAIL PARSED: Subject: {subject} | From: {sender} | Body: {body}"
                    
                    email_data = {
                        "subject": subject,
                        "from": sender,
                        "body": body,
                        "raw_headers": parsed_mail.headers
                    }
                    
                    # Log event locally
                    print(f"[*] EmailMonitor Ingested: {subject} from {sender}")
                    
                    asyncio.run_coroutine_threadsafe(
                        self.processing_queue.put({
                            "source": f"imap://{self.username}@{self.server}",
                            "content": content_str,
                            "timestamp": time.time(),
                            "type": "email",
                            "email_data": email_data
                        }),
                        self.loop
                    )
        except Exception as e:
            raise e
