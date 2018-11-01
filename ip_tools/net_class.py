from ip_tools.ip_class import IP


class NET:
    def __init__(self, net):  # net вида 192.168.0.0/24
        self.ip, self.cidr = net.split('/')

    @property
    def mask(self):
        if int(self.cidr) >= 24:
            return f"255.255.255.{256 - 2**(32-int(self.cidr))}"

    def get_octet(self, mask=None, oct_num=None):
        if mask:
            ip_by_octets = self.mask.split('.')
        else:
            ip_by_octets = self.ip.split('.')

        if oct_num is None:
            return ip_by_octets

        if 4 >= oct_num >= 1:  # если указан верный октет
            return ip_by_octets[oct_num - 1]
        else:
            return False

    def ip_in_net(self, ip):
        net_for_ip = []

        for oct in range(1, 5):
            net_for_ip.append(f"{int(ip.get_octet(oct)) & int(self.get_octet(mask=True, oct_num=oct))}")
        result = ".".join(net_for_ip)
        print(result)
        if result == self.ip:
            return True
        else:
            return False


if __name__ == '__main__':
    ip = IP('192.168.10.10')
    net = NET('192.168.10.0/24')

    print(net.ip_in_net(ip))
    print(net.mask)
