import socket
import time

host = socket.gethostbyname(socket.gethostname())
port = 9090

clients = []

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind((host, port))

_quit = False
print(f"[ Server Started ] on {host}")

while not _quit:
    try:
        data, addr = s.recvfrom(1024)

        if addr not in clients:
            clients.append(addr)

        in_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

        print(f"[*] {addr[0]}:{str(addr[1])} _ {in_time} _ ", end="")
        print(data.decode("utf-8"))

        for client in clients:
            if addr != client:
                s.sendto(data, client)
    except:    
        print("\n[ Server Stopped ]")
        _quit = True
        
s.close()
