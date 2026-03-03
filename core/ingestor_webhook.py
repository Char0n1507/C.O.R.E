import asyncio
import time
from fastapi import FastAPI, Request, HTTPException
import uvicorn


class Colors:
    FAIL = "\033[91m"
    WARNING = "\033[93m"
    ENDC = "\033[0m"


class WebhookIngestor:
    def __init__(self, host="0.0.0.0", port=8080, processing_queue=None, loop=None):
        self.host = host
        self.port = port
        self.processing_queue = processing_queue
        self.loop = loop
        self.app = FastAPI(title="C.O.R.E. Universal Webhook Ingestor")
        self.setup_routes()

    def setup_routes(self):
        @self.app.post("/ingest/splunk")
        async def ingest_splunk(request: Request):
            try:
                data = await request.json()
                content = data.get("result", data)
                await self.processing_queue.put(
                    {
                        "source": "webhook://splunk",
                        "content": str(content),
                        "timestamp": time.time(),
                        "type": "splunk_alert",
                        "raw_payload": data,
                    }
                )
                return {"status": "success"}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @self.app.post("/ingest/wazuh")
        async def ingest_wazuh(request: Request):
            try:
                data = await request.json()
                await self.processing_queue.put(
                    {
                        "source": "webhook://wazuh",
                        "content": data.get("full_log", str(data)),
                        "timestamp": time.time(),
                        "type": "wazuh_event",
                        "raw_payload": data,
                    }
                )
                return {"status": "success"}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

    async def _start_server(self):
        config = uvicorn.Config(
            self.app, host=self.host, port=self.port, log_level="error"
        )
        # uvicorn.Server.serve can call sys.exit(1) if it fails to bind.
        # We need to catch SystemExit to stop it from killing the main process.
        server = uvicorn.Server(config)
        try:
            await server.serve()
        except (Exception, SystemExit) as e:
            # We don't want to crash the main agent just because the webhook failed
            pass

    def start(self):
        print(
            f"    💡 [WEBHOOK] Listening for 3rd-party alerts on {self.host}:{self.port}"
        )
        self.loop.create_task(self._start_server())
