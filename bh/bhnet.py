import socket
import os
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


def main():
    global listen
    global port
    global command
    global upload_destination
    global execute
    global target

    usage()


if __name__ == "__main__":
    main()
