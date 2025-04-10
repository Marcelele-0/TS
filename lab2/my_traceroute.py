from scapy.all import IP, ICMP, sr1
import socket

def traceroute_scapy(target, max_hops=30, timeout=2):
    print(f"\nTraceroute to {target}, max hops: {max_hops}...\n")
    
    for ttl in range(1, max_hops + 1):
        pkt = IP(dst=target, ttl=ttl) / ICMP()
        reply = sr1(pkt, verbose=0, timeout=timeout)
        
        if reply is None:
            print(f"{ttl:2}  * * * Request timed out.")
        else:
            try:
                host = socket.gethostbyaddr(reply.src)[0]
            except socket.herror:
                host = reply.src

            print(f"{ttl:2}  {host} [{reply.src}]")

            if reply.type == 0:  # Echo Reply (destination reached)
                print(f"\nDestination {target} reached in {ttl} hops.\n")
                break

if __name__ == "__main__":
    traceroute_scapy("google.com")  # Example target")
