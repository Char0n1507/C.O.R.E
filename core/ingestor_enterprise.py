import asyncio
import time
import json
from confluent_kafka import Consumer, KafkaError

class EnterpriseKafkaMonitor:
    def __init__(self, bootstrap_servers, topics, processing_queue, loop):
        self.processing_queue = processing_queue
        self.loop = loop
        self.running = False
        
        self.consumer_conf = {
            'bootstrap.servers': bootstrap_servers,
            'group.id': 'core_soc_agent_group',
            'auto.offset.reset': 'earliest'
        }
        self.consumer = Consumer(self.consumer_conf)
        self.consumer.subscribe(topics)

    def start(self):
        """Starts the Kafka polling loop."""
        print(f"[*] Starting Enterprise Kafka Monitor on: {self.consumer_conf['bootstrap.servers']} ...")
        self.running = True
        self.task = asyncio.create_task(self._poll_kafka())

    async def _poll_kafka(self):
        while self.running:
            # Poll non-blocking via to_thread
            msg = await asyncio.to_thread(self.consumer.poll, 1.0)
            
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue # Reached end of partition
                else:
                    print(f"[!] Enterprise Kafka Error: {msg.error()}")
                    continue

            try:
                # Assuming logs come in as JSON payloads from FileBeat/Splunk
                raw_value = msg.value().decode('utf-8')
                payload = json.loads(raw_value)
                
                # Transform to standard C.O.R.E. Event
                log_content = payload.get("message", raw_value)
                source_topic = msg.topic()
                
                await self.processing_queue.put({
                    "source": f"kafka://{source_topic}",
                    "content": log_content,
                    "timestamp": time.time(),
                    "type": "enterprise_syslog"
                })
            except Exception as e:
                print(f"[!] Enterprise Kafka Parsing Error: {e}")

    def stop(self):
        """Stops the observer."""
        self.running = False
        self.consumer.close()
        print("[*] Enterprise Kafka Monitor stopped.")
