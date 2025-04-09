from packet_builder import build_packet
from packet_sender import send_packet
from packet_sniffer import sniff_icmp

def main():
    # Task 1: Build a packet
    pkt = build_packet()
    print("=== Built Packet ===")
    pkt.show()

    # Task 2: Send the packet
    print("\n=== Sending Packet ===")
    response = send_packet(pkt)
    if response:
        print("=== Response Received ===")
        response.show()
    else:
        print("No response received.")

    # Task 3: Sniff ICMP packets
    print("\n=== Sniffing ICMP Packets ===")
    sniff_icmp()

if __name__ == "__main__":
    main()