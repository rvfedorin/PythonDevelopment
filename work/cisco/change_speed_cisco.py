# ver 1.2.3
# created by Roman Fedorin

import re
import telnetlib
import paramiko
import shelve
#my
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


def get_speed(int_data):
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


def get_data_state(state):
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


def change_speed(state):
    ip_client = None
    filename = f"{settings.data_path}cl_to_change_speed.txt"
    local_clients_conf = settings.local_clients_conf
    my_key = settings.my_key
    my_key_e = settings.my_key_e
    log_string = []
    clients_not_found = []
    clients_not_done = []
    cisco_city, unix_city = get_data_state(state)

    download_clients_conf_sftp(state)

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
    tn.write(clean_str(my_key) + b"\n")
    print((tn.read_until(b">", timeout=2)).decode())
    tn.write(b"en \n")
    tn.write((clean_str(my_key_e) + b"\n"))
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

            current_speed, current_type = get_speed(int_data)

            if current_type == 'service':
                change_speed_type_service(tn, current_speed, new_speed, ip_client, interface_cl)
            elif current_type == 'rate':
                change_speed_type_rate(tn, current_speed, new_speed, ip_client, interface_cl)

            clients_not_done.append(client_ip_speed)
        # ####################################### END change speed END #######################################

            log_string.append(f"{ip_client}---------------------- \n")
            log_string.append(f"CHANGE speed {current_speed} to {new_speed} on INT {interface_cl[10]} --------- \n")
            log_string.append("======================================================================================== \n")
            ip_client[3] = None
            interface_cl[10] = None

    if len(clients_not_done) > 0:
        print('='*94)
        print('='*44, ' DONE ', '='*44)
        print(clients_not_done)
        print('='*94)
        print('='*94)
    if len(clients_not_found) > 0:
        print('='*94)
        print('='*41, ' NOT FOUNDS ', '='*41)
        print(clients_not_found)
        print('='*94)
        print('='*94)

    tn.write(b"logout \n")
    print((tn.read_until(b"#", timeout=2)).decode())
    # raw_date = str(tn.read_all())
    # str_date = raw_date.replace("\\r\\n", "\n")
    # print(str_date)

    tn.close()
    save_log.create_log(log_string, state, 'change_speed')
    return [True, clients_not_done, clients_not_found]
