from ip_tools.ip_class import IP


class NET:
    def __init__(self, net):  # net вида 192.168.0.0/24
        self.ip, self.mask = net.split('/')

    def __str__(self):
        return f'{self.ip}/{self.mask}'

    def get_octet(self, oct_num=None):
        ip_by_octets = self.ip.split('.')

        if oct_num is None:
            return ip_by_octets

        if 4 >= oct_num >= 1:  # если указан верный октет
            return ip_by_octets[oct_num - 1]
        else:
            return False

    def ip_in_net(self, ip):
        net_for_ip = []
        if ip.mask:
            for oct in range(1, 5):
                print(f"{int(ip.get_octet(oct))} & {int(self.get_octet(oct))}")
                net_for_ip.append(f"{int(ip.get_octet(oct)) & int(self.get_octet(oct))}")
            result = ".".join(net_for_ip)
            print(result)
            if result == self.ip:
                return True
            else:
                return False
        else:
            return None


if __name__ == '__main__':
    ip = IP('192.168.11.2')
    net = NET('192.168.10.0/24')

    print(net.ip_in_net(ip))
