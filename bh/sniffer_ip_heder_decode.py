import os
import socket
from ctypes import *

# host to listen on
host = "127.0.0.1"


# our ip header
class IP(Structure):
    _fields_ = [
        ("ihl", c_ubyte, 4),
        ("version", c_ubyte, 4),
        ("tos", c_ubyte),
        ("len", c_ushort),
        ("ihl", c_ushort),
        ("id", c_ushort),
        ("offset", c_ubyte),
        ("ttl", c_ubyte),
        ("sum", c_ushort),
        ("src", c_ulong),
        ("dst", c_ulong),
    ]

    def __init__(self):
        super().__init__()


if os.name == "nt":
    socket_options = socket.IPPROTO_IP
else:
    socket_options = socket.IPPROTO_ICMP

sniffer = socket.socket(socket.AF_INET, socket.SOCK_RAW)
