import asyncio
import time
import pcapy
import socket
import struct
import threading

class NetworkPacketMonitor:
    def __init__(self, interface, processing_queue, loop):
        self.interface = interface
        self.processing_queue = processing_queue
        self.loop = loop
        self.running = False

    def start(self):
        print(f"    📡 [WIFI] Activating LIVE Network Packet Sniffer on {self.interface}...")
        self.running = True
        
        # We run the sniffing in a separate thread because it blocks
        threading.Thread(target=self._sniff_traffic, daemon=True).start()

    def _get_mac(self, bytes_addr):
        return ':'.join(map('{:02x}'.format, bytes_addr))

    def _sniff_traffic(self):
        try:
            # max_bytes, promiscuous, read_timeout
            cap = pcapy.open_live(self.interface, 65536, 1, 100)
            
            # Filter to just grab standard IP packets (TCP/UDP/ICMP) to avoid flooding the LLM
            # Just grab traffic leaving or entering the host to keep it manageable
            cap.setfilter('ip')
            
            while self.running:
                (header, packet) = cap.next()
                if packet:
                    self._parse_packet(packet)
                    
        except Exception as e:
            print(f"[!] Wifi Sniffing Error: You may need root/sudo privileges to capture raw packets. Details: {e}")

    def _parse_packet(self, packet):
        try:
            # Parse Ethernet Header (14 bytes)
            eth_length = 14
            eth_header = packet[:eth_length]
            eth_data = struct.unpack('!6s6sH', eth_header)
            eth_protocol = socket.ntohs(eth_data[2])

            # Parse IP packets (Eth Protocol 8)
            if eth_protocol == 8:
                ip_header = packet[eth_length:20+eth_length]
                iph = struct.unpack('!BBHHHBBH4s4s', ip_header)

                version_ihl = iph[0]
                ihl = version_ihl & 0xF
                iph_length = ihl * 4

                ttl = iph[5]
                protocol = iph[6]
                s_addr = socket.inet_ntoa(iph[8])
                d_addr = socket.inet_ntoa(iph[9])

                protocol_name = "UNKNOWN"
                src_port = "?"
                dst_port = "?"
                
                # TCP Protocol
                if protocol == 6:
                    protocol_name = "TCP"
                    t = iph_length + eth_length
                    tcp_header = packet[t:t+20]
                    tcph = struct.unpack('!HHLLBBHHH', tcp_header)
                    src_port = tcph[0]
                    dst_port = tcph[1]
                
                # UDP Protocol
                elif protocol == 17:
                    protocol_name = "UDP"
                    u = iph_length + eth_length
                    udph_length = 8
                    udp_header = packet[u:u+8]
                    udph = struct.unpack('!HHHH', udp_header)
                    src_port = udph[0]
                    dst_port = udph[1]
                    
                # ICMP Protocol
                elif protocol == 1:
                    protocol_name = "ICMP"

                log_content = f"WIFI_SNIFF: {protocol_name} Traffic | {s_addr}:{src_port} -> {d_addr}:{dst_port}"
                
                # Pass back to async queue cleanly
                self.loop.call_soon_threadsafe(
                    self._enqueue, log_content
                )
        except Exception as e:
            pass # Silently drop malformed packets

    def _enqueue(self, content):
        asyncio.create_task(
            self.processing_queue.put({
                "source": f"pcap://{self.interface}",
                "content": content,
                "timestamp": time.time(),
                "type": "wifi_traffic"
            })
        )

    def stop(self):
        self.running = False
        print(f"[*] Wifi Monitor on {self.interface} stopped.")
