import asyncio
import time
import json
from kafka import KafkaConsumer

class EnterpriseKafkaMonitor:
    def __init__(self, bootstrap_servers, topics, processing_queue, loop):
        self.processing_queue = processing_queue
        self.loop = loop
        self.running = False
        self.bootstrap_servers = bootstrap_servers
        self.topics = topics
        self.consumer = None

    def start(self):
        """Starts the Kafka polling loop."""
        print(f"[*] Starting Enterprise Kafka Monitor on: {self.bootstrap_servers} ...")
        
        # Connect to Kafka (blocking initial connection in a thread is safer)
        try:
            self.consumer = KafkaConsumer(
                *self.topics,
                bootstrap_servers=self.bootstrap_servers,
                group_id='core_soc_agent_group',
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                value_deserializer=lambda x: x.decode('utf-8')
            )
        except Exception as e:
            print(f"[!] Failed to connect to Enterprise Kafka: {e}")
            return
            
        self.running = True
        self.task = asyncio.create_task(self._poll_kafka())

    async def _poll_kafka(self):
        while self.running:
            try:
                # poll in thread to avoid blocking asyncio loop
                partitions = await asyncio.to_thread(self.consumer.poll, timeout_ms=1000)
                
                for topic_partition, messages in partitions.items():
                    for msg in messages:
                        try:
                            # Try parsing as JSON if it's structured
                            payload = json.loads(msg.value)
                            log_content = payload.get("message", msg.value)
                        except json.JSONDecodeError:
                            # Fallback to raw string
                            log_content = msg.value
                        
                        await self.processing_queue.put({
                            "source": f"kafka://{msg.topic}",
                            "content": log_content,
                            "timestamp": time.time(),
                            "type": "enterprise_syslog"
                        })
            except Exception as e:
                print(f"[!] Enterprise Kafka Polling Error: {e}")
                await asyncio.sleep(5)

    def stop(self):
        """Stops the observer."""
        self.running = False
        if self.consumer:
            self.consumer.close()
        print("[*] Enterprise Kafka Monitor stopped.")
