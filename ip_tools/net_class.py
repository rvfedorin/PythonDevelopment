from ip_tools.ip_class import IP


class NET:
    def __init__(self, net):  # net вида 192.168.0.0/24
        self.ip, self.cidr = net.split('/')

    @property
    def mask(self):
        if int(self.cidr) < 8:
            return f"{256 - 2**(8-int(self.cidr))}.0.0.0"
        elif int(self.cidr) < 16:
            return f"255.{256 - 2**(16-int(self.cidr))}.0.0"
        elif int(self.cidr) < 24:
            return f"255.255.{256 - 2**(24-int(self.cidr))}.0"
        elif int(self.cidr) < 32:
            return f"255.255.255.{256 - 2**(32-int(self.cidr))}"

    def get_octet(self, oct_num=None, mask=None):
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

    def include_nets(self, in_cidr):
        if int(in_cidr) > int(self.cidr):
            if int(in_cidr) < 8:
                return f"{256 - 2**(8-int(self.cidr))}.0.0.0"
            elif int(in_cidr) < 16:
                return f"255.{256 - 2**(16-int(self.cidr))}.0.0"
            elif int(in_cidr) < 24:
                return f"255.255.{256 - 2**(24-int(self.cidr))}.0"
            elif int(in_cidr) < 32:
                _last = int(self.get_octet(4))
                result = []
                while _last <= (256 - 2 ** (32 - int(in_cidr))):
                    _lan = f"{self.get_octet(1)}.{self.get_octet(2)}.{self.get_octet(3)}.{_last}/{in_cidr}"
                    result.append(_lan)
                    _last += 2 ** (32 - int(in_cidr))
                return result
        else:
            return False


if __name__ == '__main__':
    ip = IP('192.168.10.10')
    net = NET('192.168.10.0/24')

    # print(net.ip_in_net(ip))
    # print(net.mask)

    for i in net.include_nets(25):
        print(i)
