# ver 1.6.5
# created by Roman Fedorin

import telnetlib
import shelve
import paramiko
from work.tools import save_log
from work import settings


def clean_str(my_string):
    for x in '!JM*FD^K11:345(_8-9)':
        my_string = my_string.replace(x, '')
    return my_string.encode('UTF-8')[::-1]


def clean_str_two(my_string):
    for x in 'JM*FD^K11:345(_8-9)':
        my_string = my_string.replace(x, '')
    return my_string[::-1]


def get_data_state(state):
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


def download_clients_conf_sftp(state):
    local_clients_conf = settings.local_clients_conf
    remote_path = settings.clients_conf_path
    port = 22
    cisco_city, unix_city = get_data_state(state)
    transport = paramiko.Transport(unix_city, port)
    transport.connect(username='support', password=clean_str_two(settings.p_un_sup))
    sftp = paramiko.SFTPClient.from_transport(transport)

    sftp.get(remote_path, local_clients_conf)
    # sftp.put(local_path, remote_path)

    sftp.close()
    transport.close()


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


def delete_from_cisco(state, client_list):
    ip_client = None
    log_string = []
    clients_not_found = []
    if_many_ip = []
    local_clients_conf = settings.local_clients_conf
    my_key = settings.my_key
    my_key_e = settings.my_key_e
    download_clients_conf_sftp(state)
    cisco_city, unix_city = get_data_state(state)

    with open(local_clients_conf) as fc:
        clients_conf = fc.read().splitlines()
        clients_conf = list(filter(None, clients_conf))

    tn = telnetlib.Telnet(cisco_city)
    print("Telnet to " + cisco_city)
    tn.write(b"\n")
    print((tn.read_until(b"Password:", timeout=2)).decode())
    tn.write(clean_str(my_key) + b"\n")
    print((tn.read_until(b">", timeout=2)).decode())
    tn.write(b"en \n")
    tn.write((clean_str(my_key_e) + b"\n"))

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
                delete_if_ip(tn, _ip, interface_cl)
        elif lan == 'lan':
            delete_if_lan(tn, ip_client, interface_cl)
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

        save_log.create_log(log_string, state, 'delete_vlan_cisco')
    return log_string


if __name__ == '__main__':
    from work.tools.customers import Customer
    state = 'Orel'

    cl_data = [state, 'Orel-Invento', 1228, '172.16.43.86', 15, 'T']
    client = Customer(*cl_data)

    for i in delete_from_cisco(state, [client]):
        print(i)
