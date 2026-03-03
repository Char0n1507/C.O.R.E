import time
import random
import json
import asyncio
from datetime import datetime
from kafka import KafkaProducer


class ThreatSimulator:
    def __init__(
        self,
        log_file="test_log.txt",
        kafka_server="localhost:9092",
        kafka_topic="enterprise-logs",
    ):
        self.log_file = log_file
        self.kafka_server = kafka_server
        self.kafka_topic = kafka_topic
        self.is_running = False

        self.attack_templates = [
            "ubuntu-server sshd[123]: Failed password for root from {ip} port {port} ssh2",
            'ubuntu-server nginx: {ip} - - [{time}] "GET /admin/config.php HTTP/1.1" 404 150',
            'ubuntu-server nginx: {ip} - - [{time}] "POST /login HTTP/1.1" 200 500 "\' OR 1=1 --"',
            "ubuntu-server kernel: [1234.56] Firewall Blocked: IN=eth0 OUT= SRC={ip} DST=10.0.0.5 PROTO=TCP SPT={port} DPT=22",
            'ubuntu-server nginx: {ip} - - [{time}] "GET /etc/passwd HTTP/1.1" 403 150',
        ]

    async def run_file_simulator(self, interval=5):
        print(f"🚀 [SIMULATOR] Starting Attack Stream to {self.log_file}...")
        while self.is_running:
            ip = f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"
            port = random.randint(1024, 65535)
            timestamp = datetime.now().strftime("%d/%b/%Y:%H:%M:%S +0000")

            template = random.choice(self.attack_templates)
            log_line = template.format(ip=ip, port=port, time=timestamp)

            with open(self.log_file, "a") as f:
                f.write(f"{datetime.now().strftime('%Y/%m/%d %H:%M:%S')} {log_line}\n")

            await asyncio.sleep(interval)

    async def run_kafka_simulator(self, interval=10):
        print(f"📡 [SIMULATOR] Starting Kafka Attack Stream to {self.kafka_topic}...")
        try:
            producer = KafkaProducer(
                bootstrap_servers=[self.kafka_server],
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
        except Exception as e:
            print(f"❌ [SIMULATOR] Kafka Connection Failed: {e}")
            return

        while self.is_running:
            attack_types = ["brute_force", "log4shell", "data_exfiltration", "rce"]
            attack_type = random.choice(attack_types)
            host = random.choice(["db-prod-01", "app-srv-99", "vpn-gateway"])

            payload = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "host": host,
                "message": f"CRITICAL: Detected suspicious {attack_type} activity originating from external node.",
                "severity": "CRITICAL",
                "simulated": True,
            }

            producer.send(self.kafka_topic, payload)
            producer.flush()
            await asyncio.sleep(interval)

    def start(self):
        self.is_running = True
        loop = asyncio.get_event_loop()
        loop.create_task(self.run_file_simulator())
        loop.create_task(self.run_kafka_simulator())
