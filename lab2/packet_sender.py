from scapy.all import sr1

def send_packet(packet, timeout=10):
    """
    Sends a packet and waits for a response.

    Args:
        packet: The packet to send.
        timeout: Timeout in seconds to wait for a response.

    Returns:
        The response packet, or None if no response is received.
    """
    response = sr1(packet, timeout=timeout, verbose=0)
    return response