import threading
import paramiko
import subprocess


def ssh_user(ip, user, passw, command):
    client = paramiko.SSHClient()
    # client.load_host_keys('/homw/wolf/.ssh/known_hosts')
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    client.connect(ip, username=user, password=passw)

    ssh_session = client.get_transport().open_session()

    if ssh_session.active:
        ssh_session.exec_command(command)
        print(ssh_session.recv(1024))
    return


if __name__ == '__main__':
    ssh_user('213.170.117.222', 'user', 'pass', 'id')
