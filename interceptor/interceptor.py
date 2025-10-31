import scapy.all as scapy
import requests
import time
import logging
import threading

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

INGEST_URL = "http://127.0.0.1:8000/api/ingest/"
PACKET_BATCH_SIZE = 50
MAX_BATCH_TIME_SECONDS = 5

packet_buffer = []
buffer_lock = threading.Lock()

def get_tcp_flags(packet):
    flags = ""
    if packet.haslayer(scapy.TCP):
        if packet[scapy.TCP].flags.S:
            flags += "S"
        if packet[scapy.TCP].flags.A:
            flags += "A"
        if packet[scapy.TCP].flags.F:
            flags += "F"
        if packet[scapy.TCP].flags.R:
            flags += "R"
        if packet[scapy.TCP].flags.P:
            flags += "P"
        if packet[scapy.TCP].flags.U:
            flags += "U"
    return flags

def send_packet_batch():
    global packet_buffer
    
    batch_to_send = []
    
    with buffer_lock:
        if not packet_buffer:
            return
        
        batch_to_send = list(packet_buffer)
        packet_buffer = []
    
    if not batch_to_send:
        return

    logging.info(f"Sending batch of {len(batch_to_send)} packets...")
    try:
        response = requests.post(INGEST_URL, json={"packets": batch_to_send})
        if response.status_code == 202:
            logging.info("Batch sent successfully.")
        else:
            logging.error(f"Failed to send batch. Status: {response.status_code}, Response: {response.text}")
    except requests.exceptions.ConnectionError:
        logging.error("Connection to backend failed. Is the Django server running?")
    except Exception as e:
        logging.error(f"An error occurred while sending batch: {e}")

def process_packet(packet):
    global packet_buffer
    
    if packet.haslayer(scapy.IP):
        try:
            packet_data = {
                "source_ip": packet[scapy.IP].src,
                "dest_ip": packet[scapy.IP].dst,
                "packet_size": len(packet),
                "protocol": "UNKNOWN",
                "source_port": 0,
                "dest_port": 0,
                "tcp_flags": ""
            }

            if packet.haslayer(scapy.TCP):
                packet_data["protocol"] = "TCP"
                packet_data["source_port"] = packet[scapy.TCP].sport
                packet_data["dest_port"] = packet[scapy.TCP].dport
                packet_data["tcp_flags"] = get_tcp_flags(packet)
            
            elif packet.haslayer(scapy.UDP):
                packet_data["protocol"] = "UDP"
                packet_data["source_port"] = packet[scapy.UDP].sport
                packet_data["dest_port"] = packet[scapy.UDP].dport
            
            elif packet.haslayer(scapy.ICMP):
                packet_data["protocol"] = "ICMP"
            
            with buffer_lock:
                packet_buffer.append(packet_data)
            
            if len(packet_buffer) >= PACKET_BATCH_SIZE:
                send_packet_batch()
        
        except Exception as e:
            logging.warning(f"Error processing packet: {e}")

def main():
    logging.info("Starting Cerberus Interceptor (v3 - Corrected)...")
    logging.info("Make sure Npcap is installed on Windows.")
    logging.info("This script may require admin/root privileges to run.")
    
    def batch_timer_loop():
        while True:
            time.sleep(MAX_BATCH_TIME_SECONDS)
            send_packet_batch()
            
    timer_thread = threading.Thread(target=batch_timer_loop, daemon=True)
    timer_thread.start()
    
    try:
        scapy.sniff(prn=process_packet, store=False, iface=None)
        
    except PermissionError:
        logging.error("PermissionError: Sniffing requires root/admin privileges.")
        logging.info("Please re-run this script as an administrator.")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
    finally:
        logging.info("Interceptor shutting down. Sending final batch...")
        send_packet_batch()

if __name__ == "__main__":
    main()