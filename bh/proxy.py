import sys
import socket
import threading


def server_loop(local_host, local_port, remote_host, remote_port, receive_first):

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server.bind((local_host, local_port))
    except Exception as e:
        print(f"[!!] Failed to listening on {local_host}:{local_port}")
        print(f"[!!] Exception {e}")
        sys.exit(0)

    print(f"[*] Listening on {local_host}:{local_port}")

    server.listen(5)

    while True:
        client_socket, addr = server.accept()

        # print out the local connection information
        print(f"[==>] Receive incoming connection frim {addr[0]}:{addr[1]}")

        # start a thread to talk to the remote host
        proxy_thread = threading.Thread(target=proxy_handler,
                                        args=(client_socket, remote_host, remote_port, receive_first))
        proxy_thread.start()


def proxy_handler(client_socket, remote_host, remote_port, receive_first):
    remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    remote_socket.connect((remote_host, remote_port))

    if receive_first:
        remote_buffer = receive_from(remote_socket)
        hexdump(remote_buffer)

        # send it to our response handler
        remote_buffer = response_handler(remote_buffer)

        # if we have data to send to our local client send it
        if len(remote_buffer):
            print(f"[<==] Sending {len(remote_buffer)} bytes to localhost")
            client_socket.send(remote_buffer)

        # now lets loop and read from local,
            # send to remote, send to local
        # rinse, wash, repeat
        while True:
            # read from localhost
            local_buffer = receive_from(client_socket)

            if len(local_buffer):
                print(f"[==>] Receive {len(local_buffer)} bytes from localhost")
                hexdump(local_buffer)

                # send it to our request handler
                request_handler(local_buffer)

                # send of the data to the remote host
                remote_socket.send(local_buffer)
                print("[==>] Send to remote.")

            # receive back the response
            remote_buffer = receive_from(remote_socket)
            if len(remote_buffer):
                print(f"[<==] Receive {len(remote_buffer)} bytes from remote")
                hexdump(remote_buffer)
                remote_buffer = response_handler(remote_buffer)
                client_socket.send(remote_buffer)
                print("[<==] Send to localhost.")

            # if no more data on either side, close the connection
            if not len(remote_buffer) or len(local_buffer):
                client_socket.close()
                remote_socket.close()

                print("[*] No more data. Closing connection. ")

                break


def receive_from(connection: socket)->str:
    buffer = ''
    connection.settimeout(2)

    try:
        while True:
            data = connection.recv(4096)

            if not data:
                break

            buffer += data.decode()
    except Exception as e:
        print(e)

    return buffer


def hexdump(src, length=16):
    result = []
    digits = 4 if isinstance(src, str) else 2

    for i in range(0, len(src), length):
        s = src[i:i+length]
        hexa = b' '.join([f"{ord(x):0{digits}X}" for x in s])
        text = b''.join([x if 0x20 <= ord(x) < 0x7F else b'.' for x in s])
        result.append(b"%04X %-*s %s" % (i, length * (digits + 1), hexa, text))
        print(b'\n'.join(result))


def response_handler(buffer: str)->str:
    # before packet modification
    return buffer


def request_handler(buffer: str)->str:
    # before packet modification
    return buffer


def main():

    if len(sys.argv[1:]) != 5:
        print("Usage: proxy.py [local_host] [local_port] [remote_host] [remote_port] [receive_first]")
        print("Example: 127.0.0.1 9000 127.0.0.2 9000 True")
        sys.exit(0)

    # setup local listening parameters
    local_host = sys.argv[1]
    local_port = int(sys.argv[2])

    # remote parameters
    remote_host = sys.argv[3]
    remote_port = int(sys.argv[4])

    # this tells our proxy to connect and receive data
    # before sending to the remote host
    receive_first = True if sys.argv[5] == 'True' else False

    # now spin up our listening socket
    server_loop(local_host, local_port, remote_host, remote_port, receive_first)

