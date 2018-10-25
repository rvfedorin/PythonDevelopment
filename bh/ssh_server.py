import socket
import threading
import sys
import paramiko
import os

key_path = os.path.abspath(os.getcwd() + '/test_rsa.key')
host_key = paramiko.RSAKey(filename=key_path)


class ServerSSH(paramiko.ServerInterface):
    def __init__(self):
        self.event = threading.Event()

    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_password(self, username, password):
        if username == 'admin' and password == 'admin':
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED


server = sys.argv[1]
ssh_port = int(sys.argv[2])

try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((server, ssh_port))
    sock.listen(100)
    print("[+] Listening for connection ... ")

    client, addr = sock.accept()
except Exception as e:
    print(f"[-] Listen failed: {e}")
    sys.exit()

print("[+] Got a connection!")

try:
    bh_session = paramiko.Transport(client)
    bh_session.add_server_key(host_key)
    server = ServerSSH()

    try:
        bh_session.start_server(server=server)
    except paramiko.SSHException as e:
        print(f"[-] SSH negotiation failed. \n {e}")
        sys.exit()

    chan = bh_session.accept(10)
    print("[+] Authenticated!")
    print(chan.recv(1024).decode())
    chan.send("Welcome to bh-ssh")

    while True:
        try:
            command = input("Enter command: ").strip('\n')
            if command != 'exit':
                chan.send(command)
                print(chan.recv(1024).decode('cp866'), '\n')
            else:
                chan.send('exit')
                print("exiting")
                bh_session.close()
                raise Exception('exit')
        except KeyboardInterrupt:
            bh_session.close()

except Exception as e:
    print(f"Caught exception: {e}")
    try:
        bh_session.close()
    except:
        pass
    sys.exit()




