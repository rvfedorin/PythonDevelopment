# ver 1.7.6
# created by Roman Fedorin

from sys import exit
import threading
import queue
import re
#  My



filename = "./nodepath"


def send_command_to_sw(sw_param, clients: list, messages_queue):
    sw_port_edit = sw_param.split("-")
    n_port = len(sw_port_edit)
    _timeout = 1
    message = '\n'
    message += "_" * 98 + '\n'
    message += "=" * 20 + f" telnet to SWITCH {sw_port_edit[1]} " + "=" * (59 - len(sw_port_edit[1])) + '\n'
    message += "=" * 98 + '\n'

    tn = login_to_sw(sw_port_edit[1])

    if tn[0] is False:
        message += tn[1]
        message_dict = {sw_port_edit[1]: message}
        messages_queue.put(message_dict)
        exit()
    else:
        tn = tn[1]
    for client in clients:
        if n_port % 2 == 0:
            conf_vl = f"conf vlan {client.vlan_name} add tagged {sw_port_edit[0]}"
        else:
            conf_vl = f"conf vlan {client.vlan_name} add tagged {sw_port_edit[0]},{sw_port_edit[2]}"

        crea_vl = f"create vlan {client.vlan_name} tag {client.vlan_number}"

        tn.write(b"\n\n")
        message += (tn.read_until(b"#", timeout=_timeout)).decode()
        tn.write(bytes(crea_vl, "utf-8") + b"\n")
        message += (tn.read_until(b"#", timeout=_timeout)).decode()
        tn.write(bytes(conf_vl, "utf-8") + b"\n")
        message += (tn.read_until(b"#", timeout=_timeout)).decode()

        if sw_port_edit[1] == client.switch:
            if client.tag == "U" or client.tag == "u":
                tn.write(bytes(f"conf vlan default del {client.sw_port} \r", "utf-8"))
                message += (tn.read_until(b"#", timeout=_timeout)).decode()
                tn.write(bytes(f"conf vlan {client.vlan_name} add untagged {client.sw_port}\r", "utf-8"))
                message += (tn.read_until(b"#", timeout=_timeout)).decode()
            elif client.tag == "T" or client.tag == "t":
                tn.write(bytes(f"conf vlan {client.vlan_name} add tagged {client.sw_port}\r", "utf-8"))
                message += (tn.read_until(b"#", timeout=_timeout)).decode()

    tn.write(b'save\n')
    message += (tn.read_until(b"#", timeout=1)).decode()
    tn.write(b"logout\n")
    message += (tn.read_until(b"#", timeout=1)).decode()
    tn.close()

    if 'DGS-1210' in message:
        pattern = '(Saving all configurations.*Saving all configurations)'
        message = re.sub(pattern, 'Saving all configurations.', message)

    # message = re.sub('Command:.*', '', message)
    message_dict = {sw_port_edit[1]: message}
    messages_queue.put(message_dict)


def format_order_message(_queue, string_sw):
    _error = []
    list_sw = string_sw.split("--")

    all_log_dict = dict()
    for mess in list(_queue.queue):
        all_log_dict.update(mess)

    all_log_list = list()
    for sw_port in list_sw:
        switch = sw_port.split('-')[1]
        all_log_list.append(all_log_dict[switch].replace('\r', ''))
        _to_print = all_log_dict[switch].replace('\r', '')
        if 'exist' in _to_print:
            _error.append(f'\nVlan exist on: {switch} - See log.')
        elif 'Timeout telnet to' in _to_print:
            _error.append(f'Timeout telnet to {switch}')
        elif 'DES-2108' in _to_print:
            _error.append(f'Error {switch} is DES-2108')

        for _ in _to_print.split('\n'):
            print(_.strip(), '')
    return [all_log_list, _error]


def create_vlan(clients, chek=None):

    if type(clients) is list:
        client = clients[0]
    else:
        client = clients
        clients = [clients]

    """ Function creates vlan """
    if client.all_path[0] is False:
        return client.all_path

    print('=' * 80, end='')
    print(client)
    print('=' * 80)

    if chek == 'None':
        chek = input('Is the data correct? (y/n): ')

    if chek in "nN":
        print('The program stopped by the user')
        exit()
    elif chek in "yY":
        messages_queue = queue.Queue()
        list_sw = client.all_path.split("--")
        threads_list = list()
        for sw_port in list_sw:
            thred_connect_sw = threading.Thread(target=send_command_to_sw, args=(sw_port, clients, messages_queue))
            thred_connect_sw.start()
            threads_list.append(thred_connect_sw)

        for _thread in threads_list:
            _thread.join()

        all_log_list, exist = format_order_message(messages_queue, client.all_path)
        save_log.create_log(all_log_list, client.state, 'create_vlan')

        _message = ''
        for i in exist:
            _message += i

        return [True, _message]

    else:
        print('Data is incorrect! You need type y or n.')
        return [False]
