from scapy.all import sniff, IP, ICMP
from datetime import datetime

def format_packet(pkt):
    """Format packet into displayable info."""
    timestamp = datetime.fromtimestamp(pkt.time).strftime('%H:%M:%S')
    src = pkt[IP].src if IP in pkt else "?"
    dst = pkt[IP].dst if IP in pkt else "?"
    payload = bytes(pkt[ICMP].payload).decode(errors='ignore') if ICMP in pkt else "-"
    return (timestamp, src, dst, payload)

def simple_sniffer(count=5):
    print(f"\n[+] Sniffing {count} ICMP packets...\n")
    packets = sniff(filter="icmp", count=count)

    print(" ID |    Time    |     Source      ->    Destination   | Payload")
    print("----+------------+-----------------+-------------------+--------")

    for i, pkt in enumerate(packets):
        timestamp, src, dst, payload = format_packet(pkt)
        print(f" {i:2} | {timestamp} | {src:15} -> {dst:15} | {payload[:20]}")

    print("\nEnter packet ID to see full details or 'q' to quit:")
    while True:
        choice = input(">> ").strip()
        if choice.lower() == 'q':
            break
        elif choice.isdigit():
            idx = int(choice)
            if 0 <= idx < len(packets):
                packets[idx].show()
            else:
                print("Invalid ID.")
        else:
            print("Invalid input.")

if __name__ == "__main__":
    simple_sniffer()
