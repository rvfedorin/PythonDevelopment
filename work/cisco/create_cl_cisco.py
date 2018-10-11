# ver 1.0.7
# created by Roman Fedorin

import telnetlib
import shelve
import paramiko
import re
from socket import timeout
import save_log
import settings


def clean_str(my_string):
    for x in '!JM*FD^K11:345(_8-9)':
        my_string = my_string.replace(x, '')
    return my_string.encode('UTF-8')[::-1]


def clean_str_two(my_string):
    for x in 'JM*FD^K11:345(_8-9)':
        my_string = my_string.replace(x, '')
    return my_string[::-1]


def login_on_cisco(cisco):
    my_key = settings.my_key
    my_key_e = settings.my_key_e
    try:
        tn = telnetlib.Telnet(cisco)
        print("Telnet to " + cisco)
        tn.write(b"\n")
        print((tn.read_until(b"Password:", timeout=4)).decode())
        tn.write(clean_str(my_key) + b"\n")
        print((tn.read_until(b">", timeout=4)).decode())
        tn.write(b"en \n")
        tn.write((clean_str(my_key_e) + b"\n"))
    except timeout:
        return False
    return tn


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


def create_command(tn, ip_if_lan_list, client):
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
        int_loopback = get_unnumbered_loopback(tn, interface)
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


def get_free_interface(state):
    cisco_city, unix_city = get_data_state(state)

    tn = login_on_cisco(cisco_city)

    if not tn:
        return False

    tn.write(f"sh int des | inc Svobodno\r".encode())
    tn.read_until(b"#", timeout=4)
    answer = (tn.read_until(b"#", timeout=4)).decode()
    return answer


def create_on_cisco(state, client):
    ip_client = None
    log_string = []
    clients_not_found = []
    if_many_ip = []
    local_clients_conf = settings.local_clients_conf
    download_clients_conf_sftp(state)
    cisco_city, unix_city = get_data_state(state)

    with open(local_clients_conf) as fc:
        clients_conf = fc.read().splitlines()
        clients_conf = list(filter(None, clients_conf))

    tn = login_on_cisco(cisco_city)
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

        result_create = create_command(tn, ip_speed_list, client)

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

    save_log.create_log(log_string, state, 'create_vlan_cisco')
    if result_create[0]:
        return log_string
    else:
        return result_create


if __name__ == '__main__':
    from customers import Customer
    state = 'Orel'
    cl_data = [state, 'Orel-Atlantm', 55, '172.16.49.150', 2, 'T']
    client = Customer(*cl_data)

    tn = login_on_cisco('213.170.117.253')
    ip_if_lan_list = ['31', '200', '205', '51', '30720']  # 31.200.205.51
    create_command(tn, ip_if_lan_list, client)


    # for i in create_on_cisco(state, client):
    #     print(i)

    # print(get_free_interface(state))