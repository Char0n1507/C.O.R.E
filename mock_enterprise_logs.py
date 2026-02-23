import time
import json
from kafka import KafkaProducer

def produce_logs():
    print("Waiting for Kafka to start...")
    time.sleep(5) # wait for broker
    producer = KafkaProducer(
        bootstrap_servers=['localhost:9092'],
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    
    logs = [
        {"message": "Feb 23 13:05:00 web-01 nginx: 45.133.1.20 - - [23/Feb/2026:13:05:00] \"GET /admin HTTP/1.1\" 401"},
        {"message": "Feb 23 13:05:02 auth-internal sshd[123]: Failed password for root from 192.168.10.50 port 22"},
        {"message": "Feb 23 13:05:05 web-02 apache2: error: SQL injection attempt detected in URI parameter 'id=1 UNION SELECT'"},
    ]
    
    print("[*] Simulating Enterprise Log Forwarder (Wazuh/Splunk)")
    for i, log in enumerate(logs):
        print(f" -> Forwarding to Kafka (enterprise-logs): {log}")
        producer.send('enterprise-logs', log)
        time.sleep(2)
        
    producer.flush()
    print("[*] Log forward complete.")

if __name__ == "__main__":
    produce_logs()
