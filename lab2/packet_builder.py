from scapy.all import IP, ICMP

def build_packet(dst_ip="google.com", payload="HELLO"):
    """
    Builds an ICMP packet with a custom payload.

    Args:
        dst_ip: Destination IP address (default is 8.8.8.8).
        payload: Payload to include in the packet (default is "HELLO").

    Returns:
        The constructed packet.
    """
    pkt = IP(dst=dst_ip) / ICMP() / payload
    return pkt