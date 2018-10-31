import os
import socket
import struct
from ctypes import Structure, c_ubyte, c_ushort, c_ulong


class IP(Structure):
    _fields_ = [
        ("ihl", c_ubyte, 4),
        ("version", c_ubyte, 4),
        ("tos", c_ubyte),  # 1
        ("len", c_ushort),  # 2
        ("id", c_ushort),
        ("offset", c_ushort),
        ("ttl", c_ubyte),
        ("protocol_num", c_ubyte),
        ("sum", c_ushort),
        ("src", c_ulong),  # 4
        ("dst", c_ulong),
    ]

    def __new__(cls, socket_buffer=None):
        return cls.from_buffer_copy(socket_buffer)

    def __init__(self, socket_buffer=None):
        super().__init__()

        # map protocol constants to their names
        self.protocol_map = {1: "ICMP", 6: "TCP", 17: "UDP"}

        # human readable IP addresses
        self.src_address = socket.inet_ntoa(struct.pack("<L", self.src))
        self.dst_address = socket.inet_ntoa(struct.pack("<L", self.dst))

        # human readable protocol
        try:
            self.protocol = self.protocol_map[self.protocol_num]
        except:
            self.protocol = str(self.protocol_num)


class ICMP(Structure):
    __fields__ = [
        ("type", c_ubyte),
        ("code", c_ubyte),
        ("checksum", c_ushort),
        ("unused", c_ushort),
        ("next_hope_mtu", c_ushort),
    ]

    def __new__(cls, *args, **kwargs):
        cls.from_buffer_copy(*args, **kwargs)

    def __init__(self):
        super().__init__()


if os.name == "nt":
    socket_protocol = socket.IPPROTO_IP
else:
    socket_protocol = socket.IPPROTO_ICMP

sniffer = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket_protocol)
sniffer.bind((host, 0))
sniffer.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)

if os.name == "nt":
    sniffer.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)

try:
    while True:

        # read a packet
        raw_buffer = sniffer.recvfrom(65565)[0]
        raw_ip_header = raw_buffer[0:20]

        # create an IP header from first 20 bytes of the buffer
        ip_header = IP(raw_ip_header)

        # print out the protocol that was detected and the hosts
        print(f"Protocol: {ip_header.protocol} {ip_header.src_address} -> {ip_header.dst_address}")

        if ip_header.protocol == "ICMP":

            # calculate where our ICMP packet starts
            offset = ip_header.ihl * 8
            print(f"Offset = {ip_header.ihl} * 8 = {offset}")

# Handle Ctrl+C
except KeyboardInterrupt:
    # if we are using Windwos, turn off promiscuous mode
    if os.name == "nt":
        sniffer.ioctl(socket.SIO_RCVALL, socket.RCVALL_OFF)

