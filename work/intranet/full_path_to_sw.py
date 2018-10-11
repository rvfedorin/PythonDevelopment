# Created by Fedorint Roman
# Script create path to switch
# ver 1.8.3

from re import findall, sub, search
from sys import exc_info
from telnetlib import Telnet
from socket import timeout
import settings
import parse_web


def port_without_link(msg):
    data_list = msg.split('\n')
    ports_down = []
    for line in data_list:
        if 'Link Down' in line or 'LinkDown' in line:
            line = line.strip()
            port_line = line.split(' ')
            port = search('^\d{1,2}', port_line[0])
            if port is not None and port.group() not in ports_down:
                ports_down.append(port.group())
    return ports_down


def has_vlan(msg):
    """ has it vlan """
    _trace = False
    data_list = msg.split('\n')
    start_read = 7 if 'DGS-1210' in str(data_list) else 6
    if _trace: print(f"----data_list-----\n{data_list}\n----data_list END-----")
    vlan_on_port = []

    for line in data_list[start_read:-1]:
        line = line[4:].strip() if start_read == 6 else line.strip()
        if _trace: print(f"----line-----\n{line}\n----line END-----")
        vlan = search('^\d{1,4}', line)
        if _trace: print(f"----vlan-----\n{vlan}\n----vlan END-----")
        if vlan is not None:
            vlan_on_port.append(vlan.group())
    if not len(vlan_on_port) == 0 and (len(vlan_on_port) > 1 or int(vlan_on_port[0]) != 1):
        print('True, has vlan', vlan_on_port)
        return True
    else:
        print('False, has no vlan')
        return False


def _bulk(self, cmd, opt):
    pass


def clean_str(my_string):
    for x in '!JM$FDK123456789':
        my_string = my_string.replace(x, '')
    return my_string.encode('UTF-8')[::-1]


def login_to_sw(sw):
    model = parse_web.get_model_sw(sw)
    if model == 'DES-2108':
        message = f'{sw} is DES-2108  \n ERROR \n'
        return [False, message]

    login = b"admin"
    passw = settings.p_sw

    try:
        print(f'Try connect to sw {sw}')
        tn = Telnet(sw, 23, 5)
        tn.set_option_negotiation_callback(_bulk)
    except timeout:
        message = f"Timeout telnet to {sw} \n ERROR \n"
        return [False, message]

    tn.read_until(b":", timeout=1)
    tn.write(login + b"\r")
    tn.read_until(b":", timeout=1)
    tn.write(clean_str(passw) + b"\r")
    tn.read_until(b"#", timeout=2)
    tn.write(b"\n\n")
    tn.read_until(b'#')
    return [True, tn]


def find_free_port(sw):
    all_free_ports = []
    tn = login_to_sw(sw)
    if tn[0] is False:
        return False
    else:
        tn = tn[1]
    tn.write(b"sh ports\n")
    tn.write(b"n\n")
    tn.write(b"n\n")
    tn.write(b"n\n")
    tn.write(b"q\n")
    msg = (tn.read_until(b'#').decode())
    p = port_without_link(msg)
    msg = (tn.read_until(b'#').decode())

    for port in p:
        print(f'checked the port {port} without link')
        command = f"show vlan ports {port}\n"
        # msg = (tn.read_until(b'#').decode())
        tn.write(b"\n")
        tn.write(command.encode())
        msg += (tn.read_until(b'#', timeout=1).decode())
        msg += (tn.read_until(b'#', timeout=1).decode())
        port_has_vlan = has_vlan(msg)
        # print(msg)
        if port_has_vlan is False:
            all_free_ports.append(port)

        msg = ''

    tn.write(b"logout\n")
    tn.close()
    return all_free_ports


def format_connect(path_up, for_switch):
    """creates a line of the form '-172.16.48.254-2--12'"""

    path_up = findall('\d+', path_up)

    if len(path_up) < 6:
        print(f'There is no connection port on switch {for_switch}')
        result = None
    else:
        ip_upstream_swith = f'{path_up[1]}.{path_up[2]}.{path_up[3]}.{path_up[4]}'  # 1-2-3-4 octets;
        result = f"-{ip_upstream_swith}-{path_up[0]}--{path_up[5]}"  # IP; 0-up port me; 5-up port UP
    return result


def up_switch_connect(path_up):  # argument is string with UP connection view 'via 28 port 172.16.41.2  to 28 port'
    path_up = findall('(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', path_up)
    return path_up[0]


def looking_ip(ip_up_connect, stolbec_ip):  # stolbec_ip - list of all ip
    path_and_ip_up = []
    try:
        ip_path_temp = sub(r'\d{0,2}/', '', stolbec_ip[ip_up_connect])  # remove '0/' if this exist in the designation
    except KeyError:
        return False

    formated_connect = format_connect(ip_path_temp, ip_up_connect)  # '-172.17.152.190-7--1'
    if formated_connect is None:
        print(f'broken path = {path_and_ip_up}')
        return False
    path_and_ip_up.append(formated_connect)
    path_and_ip_up.append(up_switch_connect(stolbec_ip[ip_up_connect]))
    return path_and_ip_up


def full_path(look_for_sw, stolbec_ip, root_port, root_sw, name_op):
    full_path_string = ''
    full_path_string += f"-{look_for_sw}"

    i = 0
    while look_for_sw != root_sw and i < 20:
        try:
            temp_path = looking_ip(look_for_sw, stolbec_ip)
            if not temp_path:
                error_string = 'Broken chain path.'
                return [False, error_string]
            full_path_string = temp_path[0] + full_path_string
            look_for_sw = temp_path[1]
            i += 1
        except TypeError:
            error_string = f"""

            ----Error in file \'full_path_to_sw.py\' line {exc_info()[2].tb_lineno}----
            ----Switch {look_for_sw} NOT FOUND in the intranet {name_op}----

            """
            print(error_string)
            return [False, error_string]

    return [True, root_port + full_path_string]


def type_connection(full_path_switch: str):
    # full_path_switch = 28-172.16.48.254-10--26-172.16.43.238-4--1-172.17.155.10

    _trace = False

    _speed = {'10G': 'TenG', '1000M': 'Gi', '100M': 'Fa'}
    new_path = ''
    full_path_switch = full_path_switch.split('--')
    for switch in full_path_switch:
        switch_ports = switch.split('-')

        tn = login_to_sw(switch_ports[1])
        if tn[0] is False:
            return [False, f'Error connect to {switch_ports[1]}']
        else:
            tn = tn[1]

        if len(switch_ports) > 2:
            port_up = f'sh ports {switch_ports[0]}\n'
            port_down = f'sh ports {switch_ports[2]}\n'
            tn.write(port_up.encode())
            tn.write(b"q\n")
            port_up = (tn.read_until(b'#').decode())
            tn.read_until(b'#')
            tn.write(port_down.encode())
            tn.write(b"q\n")
            # tn.write(b"\n\n")
            port_down = (tn.read_until(b'#').decode())
        else:
            port_up = f'sh ports {switch_ports[0]}\n'
            tn.write(port_up.encode())
            tn.write(b"q\n")
            tn.write(b"q\n")
            port_up = (tn.read_until(b'#').decode())
            switch_ports.append('Client.')
            port_down = '-?-)'

        if _trace: print(f'=====START===UP===\n{port_up}\n======END===UP==')
        if _trace: print(f'=====START===DOWN===\n{port_down}\n======END===DOWN==')
        # port_up = '(Fa)' if '100M' in port_up else '(Gi)' if '1000M' in port_up else '?'
        # port_down = '(Fa)-->' if '100M' in port_down else '(Gi)-->' if '1000M' in port_down else '?'

        for key in _speed:
            if key in port_up:
                port_up = _speed[key]

            if key in port_down:
                port_down = f'{_speed[key]})-->'

        if len(port_up) > 10: port_down = '?'
        if len(port_down) > 10: port_down = '?)-->'

        connect = f'({switch_ports[0]}{port_up})-{switch_ports[1]}-({switch_ports[2]}{port_down}'

        tn.write(b"logout\n")
        tn.close()
        new_path += connect
    if _trace: print(f'===========\n{new_path}\n===========')
    return [True, new_path]


if __name__ == '__main__':
    from xlrd import open_workbook
    import time

    start = time.time()

    ip_pattern = '\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'
    ip_and_path = dict()
    ip_and_up = []
    ended_switch = "172.16.43.114"
    excel_data_file = open_workbook('C:\INTRANETS\Orel\Intranet-Orel.xls')
    root_sw = "172.16.48.254"
    root_port = "28"
    col_sw = 2
    #
    # ended_switch = "172.16.16.134"
    # excel_data_file = open_workbook('C:\INTRANETS\Kaluga\Intranet-Kaluga.xls')
    # root_sw = "172.16.12.254"
    # root_port = "1"
    # col_sw = 2
    # ========================================== ==========================================
    # sheet = excel_data_file.sheet_by_index(0)
    # row_number = sheet.nrows
    #
    # if row_number > 0:
    #     for row in range(0, row_number):
    #         column_ip = str(sheet.row_values(row)[col_sw]).strip()
    #         stolbec_ip_up = str(sheet.row_values(row)[col_sw + 1])
    #         if not stolbec_ip_up:
    #             continue
    #         ip_and_path[column_ip] = stolbec_ip_up
    # else:
    #     print("Excel файл с данными пустой или заполнен не верно")
    #
    # # column_ip = list(filter(None, ip_and_path))
    # column_ip = ip_and_path
    # all_path = full_path(ended_switch, column_ip, root_port, root_sw, 'Orel')
    #
    # end = time.time()
    # print(all_path)
    # print(end - start)
    # ==========================================
    sw = '172.17.86.154'
    print(find_free_port(sw))
    # ============================================
    # print(type_connection('28-172.16.48.254-10--26-172.16.43.238-4--1-172.17.155.106'))


# print('\n'.join(batch_Names_wanted))
# 28-172.16.48.254-19--28-172.16.49.46-24--1-172.16.49.38-9--8-172.16.43.226-10--18-172.17.126.242-16--1-172.17.237.126-10--10-172.17.126.166
# 28-172.16.48.254-19--28-172.16.49.46-24--1-172.16.49.38-9--8-172.16.43.226-10--18-172.17.126.242-16--1-172.17.237.126-10--10-172.17.126.166
# 28-172.16.48.254-19--28-172.16.49.46-24--1-172.16.49.38-9--8-172.16.43.226-10--18-172.17.126.242-16--1-172.17.237.126-10--10-172.17.126.166

# 28-172.16.48.254-10--26-172.16.43.238-4--1-172.17.155.106-3--1-172.17.155.110-9--1-172.17.155.246-3--1-172.17.238.38
# 28-172.16.48.254-10--26-172.16.43.238-4--1-172.17.155.106-3--1-172.17.155.110-9--1-172.17.155.246-3--1-172.17.238.38

