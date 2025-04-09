from scapy.all import sniff

def sniff_icmp(count=5):
    """
    Sniffs ICMP packets.

    Args:
        count: Number of ICMP packets to capture (default is 5).

    Returns:
        A list of captured packets.
    """
    print(f"Sniffing {count} ICMP packets...")
    packets = sniff(filter="icmp", count=count, prn=lambda pkt: pkt.summary())
    return packets