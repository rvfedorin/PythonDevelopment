import paramiko
import random


class CreateMobibox:
    def __init__(self, ip, passw):
        self.ip = ip
        self.passs = passw
        self.login = b'admin'
        self.l2tp_ip = None
        self.l2tp_client_mnemo = None
        self.l2tp_client_ip = None
        self.l2tp_client_vlan = None
        self.l2tp_client_pass = None

    def ssh_connect(self):
        pass

    def create_l2tp_cl(self):
        self.l2tp_client_pass = self.gen_pass()
        l2tp_create_commane = f'ppp sec add name="{self.l2tp_client_mnemo}" ' \
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

        return [True, return_command]

    @staticmethod
    def gen_pass(num=12):
        abc = "qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM1234567890"
        new_pass = ''

        while num:
            num -= 1
            new_pass += random.choice(abc)

        return new_pass


if __name__ == '__main__':
    mb = CreateMobibox("ip", "pass")
    mb.l2tp_client_mnemo = 'TestMnemo'
    mb.l2tp_client_ip = "testIP"
    mb.l2tp_client_vlan = "123123"

    print(mb.gen_pass())
    print(mb.create_l2tp_cl()[1])
