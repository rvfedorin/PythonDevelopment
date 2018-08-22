import socket
import threading
import time

key = 8194

shutdown = False
join = False
server = ("192.168.1.253", 9090)


def _receiving(name, sock):
    while not shutdown:
        try:
            while True:
                data, addr = sock.recvfrom(1024)
                # Begin
                decrypt = ""
                k = False
                for symbol in data.decode("utf-8"):
                    if symbol == ":":
                        k = True
                        decrypt += symbol
                    elif k is False or symbol == " ":
                        decrypt += symbol
                    else:
                        decrypt += chr(ord(symbol) ^ key)
                print(decrypt)
                # End
                time.sleep(0.2)
        except:
            pass


host = socket.gethostbyname(socket.gethostname())
port = 0

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind((host, port))
s.setblocking(0)

alias = input("Name: ")

rT = threading.Thread(target=_receiving, args=("RecvThread", s))
rT.start()

while not shutdown:
    if not join:
        s.sendto(("["+alias + "] => join chat ").encode("utf-8"), server)
        join = True
    else:
        try:
            message = input('')

            # Begin
            crypt = ""
            for i in message:
                crypt += chr(ord(i) ^ key)
            message = crypt
            # End

            if message != "":
                s.sendto(("["+alias + "] :: "+message).encode("utf-8"), server)
            
            time.sleep(0.2)
        except:
            s.sendto(("["+alias + "] <= left chat ").encode("utf-8"), server)
            shutdown = True

rT.join()
s.close()
