# ver 1.0.0
# created by Roman Fedorin

import telnetlib
import shelve
import paramiko
import re
import os
from socket import timeout
from work.tools import save_log
from work import settings


class CiscoCreate:
    def __init__(self, _my_key, _my_key_e, _p_un_sup, city_pref):
        self.my_key = _my_key.encode()
        self.my_key_e = _my_key_e.encode()
        self.p_un_sup = _p_un_sup.encode()
        self.city_pref = city_pref
        self.city_shelve = settings.city_shelve
        print(f"Создан интерфейс Cisco для ОП {self.city_pref}")

    # ФУНКЦИИ УДАЛЕНИЯ
    def get_data_state(self):
        state = self.city_pref
        cisco_city = unix_city = None
        city_shelve = settings.city_shelve
        with shelve.open(city_shelve) as db:
            if state in db:
                city_db = db[state]
                temp_cisco = city_db['unix'].split('.')
                temp_cisco[3] = str(int(temp_cisco[3]) - 1)
                cisco_city = '.'.join(temp_cisco)
                unix_city = city_db['unix']
        return cisco_city, unix_city

    def download_clients_conf_sftp(self):
        local_clients_conf = settings.local_clients_conf
        remote_path = settings.clients_conf_path
        port = 22
        cisco_city, unix_city = self.get_data_state()
        transport = paramiko.Transport(unix_city, port)
        transport.connect(username='support', password=self.p_un_sup)
        sftp = paramiko.SFTPClient.from_transport(transport)

        sftp.get(remote_path, local_clients_conf)
        # sftp.put(local_path, remote_path)

        sftp.close()
        transport.close()

    @staticmethod
    def delete_if_lan(tn, ip_client, interface_cl):
        octets = ip_client[3].split('.')
        octet4, lan = octets[3].split('/')[0], octets[3].split('/')[1]
        convert_lan = 256 - (2 ** (32 - int(lan)))
        gw_client = f'{octets[0]}.{octets[1]}.{octets[2]}.{int(octet4) + 1}'
        str_ip = f'no ip address {gw_client} 255.255.255.{convert_lan} \r'
        tn.write(b"conf t \r")
        print((tn.read_until(b"#", timeout=2)).decode())
        tn.write(f"int {interface_cl[10]} \r".encode())
        print((tn.read_until(b"#", timeout=2)).decode())
        tn.write(b"des Svobodno \r")
        print((tn.read_until(b"#", timeout=2)).decode())
        tn.write(b"shutdown \r")
        print((tn.read_until(b"#", timeout=2)).decode())
        tn.write(str_ip.encode())
        print((tn.read_until(b"#", timeout=2)).decode())
        tn.write(b"end \r")
        print((tn.read_until(b"#", timeout=2)).decode())

    @staticmethod
    def delete_if_ip(tn, _ip_client, interface_cl):
        if '/' in _ip_client[3]:
            _ip_client[3] = _ip_client[3].split('/')[0]
        tn.write(b"conf t \r")
        print((tn.read_until(b"#", timeout=2)).decode())
        tn.write(f"no ip route {_ip_client[3]} 255.255.255.255 \r".encode())
        print((tn.read_until(b"#", timeout=2)).decode())
        tn.write(("int {} \r".format(interface_cl[10])).encode())
        print((tn.read_until(b"#", timeout=2)).decode())
        tn.write(b"des Svobodno \r")
        print((tn.read_until(b"#", timeout=2)).decode())
        tn.write(b"shutdown \r")
        print((tn.read_until(b"#", timeout=2)).decode())
        tn.write(b"end \r")
        print((tn.read_until(b"#", timeout=2)).decode())

    def delete_from_cisco(self, client_list):
        ip_client = None
        log_string = []
        clients_not_found = []
        if_many_ip = []
        local_clients_conf = settings.local_clients_conf
        self.download_clients_conf_sftp()
        cisco_city, unix_city = self.get_data_state()

        with open(local_clients_conf) as fc:
            clients_conf = fc.read().splitlines()
            clients_conf = list(filter(None, clients_conf))

        tn = telnetlib.Telnet(cisco_city)
        print("Telnet to " + cisco_city)
        tn.write(b"\n")
        print((tn.read_until(b"Password:", timeout=2)).decode())
        tn.write(self.my_key + b"\n")
        print((tn.read_until(b">", timeout=2)).decode())
        tn.write(b"en \n")
        tn.write(self.my_key_e + b"\n")

        for client in client_list:  # List of clients to delete

            for cl_ip_line in clients_conf:  # Ischem IP klienta
                #  cl_ip_line = 'Orel-PlemzavMB in 4096 77.235.218.248 -unnumbered'
                cl_ip_line_mnemo = cl_ip_line.split()

                if len(cl_ip_line_mnemo) > 0:
                    if cl_ip_line_mnemo[0] == client.vlan_name:
                        ip_client = cl_ip_line_mnemo
                        if_many_ip.append(ip_client)
                    else:
                        continue
                else:
                    continue

            if ip_client is None:
                clients_not_found.append(client.vlan_name)
                continue

            ip_if_lan_list = ip_client[3].split('.')
            ip_oct4 = ip_if_lan_list[3].split('/')

            if ip_if_lan_list[3].find('/') >= 0 and int(ip_oct4[1]) != 32:
                ip_gw_oct4 = int(ip_oct4[0]) + 1
                ip_gw_lan = f'{ip_if_lan_list[0]}.{ip_if_lan_list[1]}.{ip_if_lan_list[2]}.{ip_gw_oct4}'

                # result: ['sh', 'ip', 'int', 'br', '|', 'inc', '172.16.44.121', 'Te0/3/0.867',
                # '172.16.44.121', 'YES', 'manual', 'administratively', 'down', 'down', 'CiscoOrelASR1002#']
                command_string = ("sh ip int br | inc {} \r".format(ip_gw_lan)).encode()
                lan = 'lan'
            else:
                ip_if_lan_list[3] = ip_if_lan_list[3].replace('/32', '')
                ip_full = f'{ip_if_lan_list[0]}.{ip_if_lan_list[1]}.{ip_if_lan_list[2]}.{ip_if_lan_list[3]}'
                command_string = ("sh conf | sec {} 255.255.255.255 \r".format(ip_full)).encode()
                lan = 'ip'

            tn.read_until(b"#", timeout=2)
            tn.write(command_string)
            interface_cl = str((tn.read_until(b"#", timeout=2)).decode()).split()
            print(interface_cl)
            if len(interface_cl) < 10:
                clients_not_found.append(client.vlan_name)
                continue
            elif interface_cl[10] is None:
                clients_not_found.append(client.vlan_name)
                continue
            elif interface_cl[10] == 'Null0' and len(interface_cl) > 15:
                """ interface_cl:
                ['sh', 'conf', '|', 'sec', '95.80.120.30', '255.255.255.255', 
                 'ip', 'route', '95.80.120.30', '255.255.255.255', 'Null0',
                 'ip', 'route', '95.80.120.30', '255.255.255.255', 'TenGigabitEthernet0/3/0.928', '10',
                 'CiscoOrelASR1002#']
                """
                interface_cl[10] = interface_cl[15]

            if lan == 'lan':
                interface_cl[10] = interface_cl[7]
            # ####################################### block udaleniya START

            if lan == 'ip':
                for _ip in if_many_ip:
                    self.delete_if_ip(tn, _ip, interface_cl)
            elif lan == 'lan':
                self.delete_if_lan(tn, ip_client, interface_cl)
            # ####################################### block udaleniya END

            log_string.append("=" * 88 + "\n")
            log_string.append(f"{ip_client}" + "="*(88-len(ip_client)) + "\n")
            log_string.append(f"DELETE CUSTOMER ON INT {interface_cl[10]} --------- \n")
            log_string.append("="*88 + "\n")
            ip_client[3] = None
            interface_cl[10] = None

            tn.write(b"logout \n")
            print((tn.read_until(b"#", timeout=2)).decode())

            tn.close()

            if len(clients_not_found) > 0:
                print('=' * 94)
                print('=' * 41, ' NOT FOUNDS ', '=' * 41)
                print(clients_not_found)
                print('=' * 94)
                print('=' * 94)

            save_log.create_log(log_string, self.city_pref, 'delete_vlan_cisco')
        return log_string

    # ФУНКЦИИ  СОЗДАНИЯ
    def login_on_cisco(self, cisco):
        try:
            tn = telnetlib.Telnet(cisco)
            print("Telnet to " + cisco)
            tn.write(b"\n")
            print((tn.read_until(b"Password:", timeout=4)).decode())
            tn.write(self.my_key + b"\n")
            print((tn.read_until(b">", timeout=4)).decode())
            tn.write(b"en \n")
            tn.write(self.my_key_e + b"\n")
        except timeout:
            return False
        return tn

    @staticmethod
    def get_unnumbered_loopback(tn, interface):
        _fail = True
        while _fail:
            tn.write(f"do sh run int {interface} \r".encode())
            answer = (tn.read_until(b"#", timeout=4)).decode()
            for row in answer.split('\n'):
                if 'ip unnumbered' in row:
                    return row[:-1]
            last = int(interface[-1])
            interface = interface[0:-1] + f'{last - 1 if last > 0 else 9}'

    def create_command(self, tn, ip_if_lan_list, client):
        _pattern_interface = '\w{2}\d{1}/(\d{1}/)?\d{1}\.\d{1,4}'
        _pattern_s = '\d{3,6}k'
        _pattern_r = '\d{4,10} \d{4,10} \d{4,10}'

        ip_cl = f'{ip_if_lan_list[0]}.{ip_if_lan_list[1]}.{ip_if_lan_list[2]}.{ip_if_lan_list[3]}'
        speed_cl = ip_if_lan_list[4]
        new_rate = int(speed_cl) / 1024
        new_speed_string = f'{int(1024000 * new_rate)} {int(192000 * new_rate)} {int(384000 * new_rate)}'

        tn.write(f"sh int des | inc {client.vlan_number} \r".encode())
        tn.read_until(b"#", timeout=4)
        answer = (tn.read_until(b"#", timeout=4)).decode()

        _search = re.search(_pattern_interface, answer)

        if _search is None:
            _error = 'Not found interface.'
            return [False, _error]
        else:
            interface = _search.group()
            interface = interface.split('.')
            interface = interface[0] + f'.{client.vlan_number}'

        tn.write(f"sh run int {interface} \r".encode())  # intrface = 'Gi0/0.122'
        answer = (tn.read_until(b"#", timeout=4)).decode()
        print(answer)
        _search = re.search(_pattern_s, answer)
        if _search is None:
            _search = re.search(_pattern_r, answer)
            if _search is None:
                _error = 'Not found speed on interface.'
                return [False, _error]
            else:
                res = ['rate', _search.group()]
        else:
            res = ['service', _search.group()]

        tn.write(b"conf t \r")
        print((tn.read_until(b"#", timeout=4)).decode())
        tn.write(f"ip route {ip_cl} 255.255.255.255 {interface} 10 \r".encode())
        print((tn.read_until(b"#", timeout=4)).decode())
        tn.write(f"int {interface} \r".encode())

        if 'ip unnumbered' in answer:
            pass
        else:
            int_loopback = self.get_unnumbered_loopback(tn, interface)
            tn.write(f"{int_loopback}\r".encode())
            print((tn.read_until(b"#", timeout=4)).decode())

        tn.write(f"des {client.vlan_name} \r".encode())

        if res[0] == 'service':
            tn.write(f"no service-policy input {res[1]} \r".encode())
            print((tn.read_until(b"#", timeout=4)).decode())
            tn.write(f"no service-policy output {res[1]} \r".encode())
            print((tn.read_until(b"#", timeout=4)).decode())

            tn.write(f"service-policy input {speed_cl}k \r".encode())
            print((tn.read_until(b"#", timeout=4)).decode())
            tn.write(f"service-policy output {speed_cl}k \r".encode())
            print((tn.read_until(b"#", timeout=4)).decode())
        else:
            tn.write(f"no rate-limit input {res[1]} conform-action transmit exceed-action drop \r".encode())
            tn.read_until(b"#", timeout=4)
            tn.write(f"no rate-limit output {res[1]} conform-action transmit exceed-action drop \r".encode())
            print((tn.read_until(b"#", timeout=4)).decode())

            tn.write(f"rate-limit input {new_speed_string} conform-action transmit exceed-action drop \r".encode())
            tn.read_until(b"#", timeout=4)
            tn.write(f"rate-limit output {new_speed_string} conform-action transmit exceed-action drop \r".encode())
            print((tn.read_until(b"#", timeout=4)).decode())

        tn.write(b"no shutdown \r")
        print((tn.read_until(b"#", timeout=4)).decode())
        tn.write(b"end \r")
        print((tn.read_until(b"#", timeout=4)).decode())
        return [True, 'Success created.']

    def get_free_interface(self):
        cisco_city, unix_city = self.get_data_state()

        tn = self.login_on_cisco(cisco_city)

        if not tn:
            return False

        tn.write(f"sh int des | inc Svobodno\r".encode())
        tn.read_until(b"#", timeout=4)
        answer = (tn.read_until(b"#", timeout=4)).decode()
        return answer

    def create_on_cisco(self, client):
        ip_client = None
        log_string = []
        clients_not_found = []
        if_many_ip = []
        local_clients_conf = settings.local_clients_conf
        self.download_clients_conf_sftp()
        cisco_city, unix_city = self.get_data_state()

        with open(local_clients_conf) as fc:
            clients_conf = fc.read().splitlines()
            clients_conf = list(filter(None, clients_conf))

        tn = self.login_on_cisco(cisco_city)
        if not tn:
            return False

        for cl_ip_line in clients_conf:  # Ischem IP klienta
            #  cl_ip_line = 'Orel-PlemzavMB in 4096 77.235.218.248 -unnumbered'
            cl_ip_line_mnemo = cl_ip_line.split()

            if len(cl_ip_line_mnemo) > 0:
                if cl_ip_line_mnemo[0] == client.vlan_name:
                    ip_client = cl_ip_line_mnemo
                    if_many_ip.append(ip_client)
                else:
                    continue
            else:
                continue

        if ip_client is None:
            clients_not_found.append(client.vlan_name)
            result_create = [False]
        else:
            ip_speed_list = ip_client[3].split('.')
            ip_oct4 = ip_speed_list[3].split('/')
            ip_speed_list[3] = ip_oct4[0]
            ip_speed_list.append(ip_client[2])

            # ####################################### CREATE BLOCK START

            result_create = self.create_command(tn, ip_speed_list, client)

            # #######################################  CREATE BLOCK END

            log_string.append("=" * 88 + "\n")
            log_string.append(f"{ip_client}" + "="*(88-len(ip_client)) + "\n")
            log_string.append(f"CREATE CUSTOMER ON INT {client.vlan_number} --------- \n")
            log_string.append("="*88 + "\n")
            ip_client[3] = None

            tn.write(b"logout \n")
            print((tn.read_until(b"#", timeout=4)).decode())

            tn.close()

        if len(clients_not_found) > 0:
            print('=' * 94)
            print('=' * 41, ' NOT FOUNDS ', '=' * 41)
            print(clients_not_found)
            print('=' * 94)
            print('=' * 94)

        save_log.create_log(log_string, self.city_pref, 'create_vlan_cisco')
        if result_create[0]:
            return log_string
        else:
            return result_create

    # ФУНКЦИИ СМЕНЫ СКОРОСТЕЙ
    def get_speed(self, int_data):
        b = None
        _type = None
        for a in int_data:
            if a is None:
                continue

            if 'service-policy input' in a:
                b = re.match(' service-policy input .*', a)
                _type = 'service'
            elif 'rate-limit input' in a:
                b = re.match(' rate-limit input .*', a)
                _type = 'rate'

            if b is None:
                continue

            current_speed = b.group(0).split()
            return current_speed[2], _type

    @staticmethod
    def change_speed_type_service(tn, current_speed, new_speed, ip_client, interface_cl):
        print("=" * 100)
        print("=" * 100)
        print(f"{ip_client}----------------------")
        print(f"CHANGE speed {current_speed} to {new_speed} on INT {interface_cl[10]} ---------")
        print("=" * 100)

        print((tn.read_until(b"#", timeout=2)).decode())
        tn.write(f"no service-policy input {current_speed} \r".encode())
        print((tn.read_until(b"#", timeout=2)).decode())
        tn.write(f"no service-policy output {current_speed} \r".encode())
        print((tn.read_until(b"#", timeout=2)).decode())
        tn.write(f"service-policy input {new_speed} \r".encode())
        print((tn.read_until(b"#", timeout=2)).decode())
        tn.write(f"service-policy output {new_speed} \r".encode())
        print((tn.read_until(b"#", timeout=2)).decode())
        tn.write(b"end \r")
        print((tn.read_until(b"#", timeout=2)).decode())

    @staticmethod
    def change_speed_type_rate(tn, current_speed, new_speed, ip_client, interface_cl):
        new_rate = int(new_speed.split('k')[0]) / 1024
        cur_rate = int(current_speed) / 1024000
        new_speed_string = f'{int(1024000 * new_rate)} {int(192000 * new_rate)} {int(384000 * new_rate)}'
        cur_speed_string = f'{int(1024000 * cur_rate)} {int(192000 * cur_rate)} {int(384000 * cur_rate)}'

        print("=" * 100)
        print("=" * 100)
        print(f"{ip_client}----------------------")
        print(f"CHANGE speed {current_speed} to {new_speed} on INT {interface_cl[10]} ---------")
        print("=" * 100)

        print((tn.read_until(b"#", timeout=2)).decode())
        tn.write(f"no rate-limit input {cur_speed_string} conform-action transmit exceed-action drop \r".encode())
        print((tn.read_until(b"#", timeout=2)).decode())
        tn.write(f"no rate-limit output {cur_speed_string} conform-action transmit exceed-action drop \r".encode())
        print((tn.read_until(b"#", timeout=2)).decode())
        tn.write(f"rate-limit input {new_speed_string} conform-action transmit exceed-action drop \r".encode())
        print((tn.read_until(b"#", timeout=2)).decode())
        tn.write(f"rate-limit output {new_speed_string} conform-action transmit exceed-action drop \r".encode())
        print((tn.read_until(b"#", timeout=2)).decode())
        tn.write(b"end \r")
        print((tn.read_until(b"#", timeout=2)).decode())

    def change_speed(self):
        ip_client = None
        filename = os.path.abspath(os.getcwd() + f"{settings.data_path}cl_to_change_speed.txt")

        local_clients_conf = settings.local_clients_conf
        log_string = []
        clients_not_found = []
        clients_not_done = []

        cisco_city, unix_city = self.get_data_state()

        try:
            self.download_clients_conf_sftp()
        except Exception as e:
            print(f"Не удалось загрузить Clients.conf: cisco_class->change_speed. {e}")
        else:

            with open(filename) as f:
                clients_list_to_change = f.read().splitlines()
                clients_list_to_change = list(filter(None, clients_list_to_change))

            with open(local_clients_conf) as fc:
                clients_conf = fc.read().splitlines()
                clients_conf = list(filter(None, clients_conf))

            tn = telnetlib.Telnet(cisco_city)
            print("Telnet to " + cisco_city)
            tn.write(b"\n")
            print((tn.read_until(b"Password:", timeout=2)).decode())
            tn.write(self.my_key + b"\n")
            print((tn.read_until(b">", timeout=2)).decode())
            tn.write(b"en \n")
            tn.write(self.my_key_e + b"\n")
            print((tn.read_until(b"#", timeout=1)).decode())

            for client_ip_speed in clients_list_to_change:  # Spisok klientov dlya izmeneniya
                client_ip_speed = client_ip_speed.split()  # [mnemokod][skorost]

                for cl_ip_line in clients_conf:  # Ischem IP klienta

                    cl_ip_line_mnemo = cl_ip_line.split()

                    if len(cl_ip_line_mnemo) > 0:
                        if cl_ip_line_mnemo[0] == client_ip_speed[0]:
                            print(f'Found: {cl_ip_line_mnemo}')
                            ip_client = cl_ip_line_mnemo
                            new_speed = client_ip_speed[1]
                        else:
                            continue
                    else:
                        continue

                if ip_client is None or ip_client[3] is None:
                    clients_not_found.append(client_ip_speed)
                    print(f'Not found {client_ip_speed}')
                    continue
                else:
                    ip_if_lan_list = ip_client[3].split('.')
                    ip_oct4 = ip_if_lan_list[3].split('/')

                    if ip_if_lan_list[3].find('/') >= 0 and int(ip_oct4[1]) != 32:
                        ip_gw_oct4 = int(ip_oct4[0]) + 1
                        ip_gw_lan = f'{ip_if_lan_list[0]}.{ip_if_lan_list[1]}.{ip_if_lan_list[2]}.{ip_gw_oct4}'
                        command_string = ("sh arp | sec {} \r".format(ip_gw_lan)).encode()
                    else:
                        ip_if_lan_list[3] = ip_if_lan_list[3].replace('/32', '')
                        ip_full = f'{ip_if_lan_list[0]}.{ip_if_lan_list[1]}.{ip_if_lan_list[2]}.{ip_if_lan_list[3]}'
                        command_string = ("sh conf | sec {} 255.255.255.255 \r".format(ip_full)).encode()

                    print(f'Command: {command_string} ')
                    tn.read_until(b"#", timeout=2)
                    tn.write(command_string)
                    interface_cl = str((tn.read_until(b"#", timeout=2)).decode()).split()
                    if len(interface_cl) < 10:
                        clients_not_found.append(client_ip_speed)
                        continue
                    elif interface_cl[10] is None:
                        clients_not_found.append(client_ip_speed)
                        continue

                    # ####################################### START change speed START ##################################
                    tn.write(b"conf t \r")
                    tn.read_until(b"#", timeout=2)
                    tn.write(("do sh run int {}  \r".format(interface_cl[10])).encode())
                    int_data = str((tn.read_until(b"#", timeout=2)).decode()).splitlines()

                    tn.write(("int {} \r".format(interface_cl[10])).encode())

                    current_speed, current_type = self.get_speed(int_data)

                    if current_type == 'service':
                        self.change_speed_type_service(tn, current_speed, new_speed, ip_client, interface_cl)
                    elif current_type == 'rate':
                        self.change_speed_type_rate(tn, current_speed, new_speed, ip_client, interface_cl)

                    clients_not_done.append(client_ip_speed)
                    # ####################################### END change speed END #######################################

                    log_string.append(f"{ip_client}---------------------- \n")
                    log_string.append(
                        f"CHANGE speed {current_speed} to {new_speed} on INT {interface_cl[10]} --------- \n")
                    log_string.append(
                        "======================================================================================== \n")
                    ip_client[3] = None
                    interface_cl[10] = None

            if len(clients_not_done) > 0:
                print('=' * 94)
                print('=' * 44, ' DONE ', '=' * 44)
                print(clients_not_done)
                print('=' * 94)
                print('=' * 94)
            if len(clients_not_found) > 0:
                print('=' * 94)
                print('=' * 41, ' NOT FOUNDS ', '=' * 41)
                print(clients_not_found)
                print('=' * 94)
                print('=' * 94)

            tn.write(b"logout \n")
            print((tn.read_until(b"#", timeout=2)).decode())
            # raw_date = str(tn.read_all())
            # str_date = raw_date.replace("\\r\\n", "\n")
            # print(str_date)

            tn.close()
            save_log.create_log(log_string, self.city_pref, 'change_speed')
            return [True, clients_not_done, clients_not_found]


if __name__ == '__main__':
    from work.tools.customers import Customer
    state = 'Orel'

    cl_data = [state, 'Orel-Invento', 1228, '172.16.43.86', 15, 'T']
    client = Customer(*cl_data)
    # _cis = CiscoCreate()

    # for i in _cis.delete_from_cisco([client]):
    #     print(i)
