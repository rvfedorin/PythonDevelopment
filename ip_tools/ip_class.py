class IP:
    def __init__(self, ip):
        if "/" in ip:
            self.ip, self.mask = ip.split("/")
        else:
            self.ip = ip
            self.mask = None

    def get_octet(self, oct_num=None):
        ip_by_octets = self.ip.split('.')

        if oct_num is None:
            return ip_by_octets

        if 4 >= oct_num >= 1:  # если указан верный октет
            return ip_by_octets[oct_num-1]
        else:
            return False

    def __str__(self):
        return self.ip


if __name__ == '__main__':
    ip = IP('192.168.2.2')

    print(ip)
    print(ip.get_octet())
    print(ip.get_octet(0))