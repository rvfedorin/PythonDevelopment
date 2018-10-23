import socket
import sys
import getopt
import threading
import subprocess

listen = False
command = False
upload = False
execute = ""
target = ""
upload_destination = ""
port = 0


def usage():
    print("BHP Net Tool")
    print()
    print("Usage: bhpnet.py -t target_host -p port")
    print("-l --listen               - listen on host:port for incoming connections")
    print("-e --execute=file_to_run  - execute the given file upon receiving a connection")
    print("-c --command              - initialize a command shell")
    print("-u --upload=destination   - upon receiving connection uplad a file and write to [destination]")
    print("", end="\n\n")
    print("Examples: ")
    print("bhpnet.py -t 192.168.1.1 -p 9999 -l -c")
    print("bhpnet.py -t 192.168.1.1 -p 9999 -l -u=c://target.exe")
    print("bhpnet.py -t 192.168.1.1 -p 9999 -l -e='cat /etc/pass'")
    print("echo 'ASDF' | bhpnet.py -t 192.168.1.1 -p 135")


def client_sender(buffer):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # connect to our target host
        client.connect((target, port))
        if len(buffer) > 0:
            client.send(buffer)

        while True:
            # now wait for data back
            recv_len = 1
            response = ''

            while recv_len:
                data = client.recv(4096)
                recv_len = len(data)
                response += data

                if recv_len < 4096:
                    break
            print(response)

            # wait for more input
            buffer = input("")
            buffer += "\n"

            # send it off
            client.send(buffer)

    except Exception as e:
        print(f"[*] Exception: {e}")

        # tear down the connection
        client.close()


def server_loop():
    global target

    # if not target is defined, we will listen on all interfaces
    if not len(target):
        target = '0.0.0.0'

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((target, port))
    server.listen(5)

    while True:
        client_socket, address = server.accept()

        # spin off a thread to handle our new client
        client_thread = threading.Thread(target=client_handler,
                                         args=(client_socket, ))
        client_thread.start()


def run_command(command:str):
    # trim the new line
    command = command.rstrip()

    # run the commant and get the output back
    try:
        output = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
    except Exception as e:
        output = f"Failed to execute command: \r\n{e}\r\n"

    # send the output to the client
    return output


def client_handler(client_socket):
    global upload
    global execute
    global command

    # check for upload
    if len(upload_destination):

        # read in all of the bytes and write to our destination
        file_buffer = ''

        # keep reading data until none is available
        while True:
            data = client_socket.recive(4096)

            if not data:
                break
            else:
                file_buffer += data
        # now we take these data and try to write them out
        try:
            with open(upload_destination, "wb") as file_descriptor:
                file_descriptor.write(file_buffer)
                # acknowledge that we wrote file out
                _out = f"Successfully saved file to {upload_destination}"

        except Exception as e:
                _out = f"Failed to save file {upload_destination} \n {e}"

        client_socket.send(_out)



def main():
    global listen
    global port
    global command
    global upload_destination
    global execute
    global target

    if not len(sys.argv[1:]):
        usage()

    # read the command line options
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hle:t:p:cu:",
                                   ["help", "listen", "execute", "target", "port", "command", "upload"])
    except getopt.GetoptError as err:
        print(str(err))
        usage()

    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
        elif o in ("-l", "--listen"):
            listen = True
        elif o in ("-e", "--execute"):
            execute = a
        elif o in ("-t", "--target"):
            target = a
        elif o in ("-p", "--port"):
            port = int(a)
        elif o in ("-c", "--command"):
            command = True
        elif o in ("-u", "--upload"):
            upload_destination = a
        else:
            assert False, "Unhandled Option"

    # are we going to listen or just send data from stdin?
    if not listen and len(target) and port > 0:
        # read in the buffer from commandline
        # this will block, so send Ctrl+D if not sending input
        # to stdin
        buffer = sys.stdin.read()

        # send data off
        client_sender(buffer)

    # we are going to listen and potentially
    # upload things, execute commands, and drop a shell back
    # depending on our command line options above
    if listen:
        server_loop()

    main()





if __name__ == "__main__":
    main()
