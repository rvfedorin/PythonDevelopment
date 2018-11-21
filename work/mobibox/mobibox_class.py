import paramiko
import random


class CreateMobibox:
    def __init__(self, ip, passw):
        self.ip = ip
        self.passs = passw
        self.login = 'admin'
        self.l2tp_ip = None
        self.l2tp_client_mnemo = None
        self.l2tp_client_ip = None
        self.l2tp_client_vlan = None
        self.l2tp_client_pass = None

    def create_l2tp_cl(self):
        errors = ""
        self.l2tp_client_pass = self.gen_pass()

        if self.l2tp_client_mnemo and self.l2tp_client_pass and self.l2tp_client_ip and self.l2tp_ip:
            l2tp_create_command = f'ppp sec add name="{self.l2tp_client_mnemo}" ' \
                                  f'service=l2tp password="{self.l2tp_client_pass}" ' \
                                  f'remote-address={self.l2tp_client_ip} ' \
                                  f'local-address={self.l2tp_ip}'

            eoip_create_command = f'/interface eoip add remote-address={self.l2tp_client_ip} ' \
                                  f'tunnel-id={self.l2tp_client_vlan}  ' \
                                  f'name={self.l2tp_client_mnemo} disabled=no !keepalive'

            bridge_add_command = f'/interface bridge port add ' \
                                 f'bridge=bridgeUnnumbered horizon=3 ' \
                                 f'interface={self.l2tp_client_mnemo}'

            return_command = f'/interface l2tp-client add add-default-route=yes ' \
                             f'connect-to={self.ip} disabled=no keepalive-timeout=disabled name=l2tp-out2 ' \
                             f'password={self.l2tp_client_pass} user={self.l2tp_client_mnemo}'
            return_command += '\n/ip dhcp-client set default-route-distance=10 numbers=0'

            try:
                mb_ssh = paramiko.SSHClient()
                mb_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                mb_ssh.connect(hostname=self.ip, username=self.login, password=self.passs, port=22)

                stdin, stdout, stderr = mb_ssh.exec_command(l2tp_create_command)
                # print(stdout.read().decode())
                _err = stderr.read().decode() + stdout.read().decode()
                errors += f"\nError --- {_err}" if _err else ''

                if not _err:
                    stdin, stdout, stderr = mb_ssh.exec_command(eoip_create_command)
                    # print(stdout.read().decode())
                    _err = stderr.read().decode() + stdout.read().decode()
                    errors += f"\nError --- {_err}" if _err else ''

                if not _err:
                    stdin, stdout, stderr = mb_ssh.exec_command(bridge_add_command)
                    # print(stdout.read().decode())
                    _err = stderr.read().decode() + stdout.read().decode()
                    errors += f"\nError --- {_err}" if _err else ''

            except Exception as e:
                errors += f"\nError --- {e}"
                print(f"Ошибка {e}")
        else:
            errors += f"\nFilled not all fill!"

        if not errors:
            return [True, return_command]
        else:
            return [False, errors]

    @staticmethod
    def gen_pass(num=12):
        abc = "qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM1234567890"
        new_pass = ''

        while num:
            num -= 1
            new_pass += random.choice(abc)

        return new_pass


if __name__ == '__main__':
    mb = CreateMobibox("95.80.99.173", "123")
    mb.l2tp_client_mnemo = 'TestMnemo'
    mb.l2tp_ip = "172.17.231.129"
    mb.l2tp_client_ip = "172.17.231.196"
    mb.l2tp_client_vlan = "12312"

    print(mb.gen_pass())
    print(mb.create_l2tp_cl()[1])
