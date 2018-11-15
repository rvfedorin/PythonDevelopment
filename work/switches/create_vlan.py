# ver 1.0.0
# created by Roman Fedorin

from sys import exit
import threading
import queue
import re
#  My

from switches import switch
from tools import save_log


filename = "./nodepath"


def send_command_to_sw(sw_param, clients: list, messages_queue, login='admin', passw=None):
    sw_port_edit = sw_param.split("-")
    n_port = len(sw_port_edit)

    message = '\n'
    message += "_" * 98 + '\n'
    message += "=" * 20 + f" telnet to SWITCH {sw_port_edit[1]} " + "=" * (59 - len(sw_port_edit[1])) + '\n'
    message += "=" * 98 + '\n'

    sw_obj = switch.NewSwitch(sw_port_edit[1], login, passw)

    for client in clients:
        if n_port % 2 == 0:
            conf_vl = f"conf vlan {client.vlan_name} add tagged {sw_port_edit[0]}\r"
        else:
            conf_vl = f"conf vlan {client.vlan_name} add tagged {sw_port_edit[0]},{sw_port_edit[2]}\r"

        crea_vl = f"create vlan {client.vlan_name} tag {client.vlan_number}\r"

        response = sw_obj.send_command([crea_vl, conf_vl])
        if response[0]:
            message += '\n'.join(response)
        else:
            message += f'Error on {sw_obj.ip}'

        if sw_obj.ip == client.switch:
            if client.tag == "U" or client.tag == "u":
                del_from_def = f"conf vlan default del {client.sw_port} \r"
                add_untagged = f"conf vlan {client.vlan_name} add untagged {client.sw_port}\r"
                response = sw_obj.send_command([del_from_def, add_untagged])

            elif client.tag == "T" or client.tag == "t":
                add_tagged = f"conf vlan {client.vlan_name} add tagged {client.sw_port}\r"
                _save = 'save\n'
                response = sw_obj.send_command([add_tagged, _save])

            if response[0]:
                message += '\n'.join(response)
            else:
                message += f'Error on {sw_obj.ip}'

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
        elif 'Error on' in _to_print:
            _error.append(f'\n[!!!] Error on {switch}')
        elif 'DES-2108' in _to_print:
            _error.append(f'Error {switch} is DES-2108')

        for _ in _to_print.split('\n'):
            print(_.strip(), '')
    return [all_log_list, _error]


def create_vlan(clients, chek=None, login=None, passw=None):

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
            thred_connect_sw = threading.Thread(target=send_command_to_sw,
                                                args=(sw_port, clients, messages_queue, login, passw))
            thred_connect_sw.start()
            threads_list.append(thred_connect_sw)

        for _thread in threads_list:
            _thread.join()

        all_log_list, exist = format_order_message(messages_queue, client.all_path)
        try:
            save_log.create_log(all_log_list, client.state, 'create_vlan')
        except Exception as e:
            print(f"Не удалось сохранить лог: {e}")

        _message = ''
        for i in exist:
            _message += i

        return [True, _message]

    else:
        print('Data is incorrect! You need type y or n.')
        return [False]


if __name__ == '__main__':
    from work.tools.customers import Customer
    import os

    print(os.path.abspath(os.path.dirname(__file__)))

    state = 'Orel'
    passw = input("passw: ")
    cl_data = [state, '4001', 4000, '172.16.47.122', 15, 'T']
    client = Customer(*cl_data)
    create_vlan(client, 'y', login='admin', passw=passw)