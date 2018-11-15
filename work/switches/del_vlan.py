# ver 1.0.0
# created by Roman Fedorin

# from sys import exit
from tools import save_log
from switches import switch


def op_define(mnemokod):
    temp = mnemokod.split('-')
    return temp[0]


# string_sw is the full path to the desired switch from the file nodepath
def del_code(clients, **kwargs):
    correct_cl = kwargs.get('correct_cl', 'y')
    que = kwargs.get('que', None)
    login = kwargs.get('login', 'admin')
    passw = kwargs.get('passw', None)

    if isinstance(clients, tuple):
        que = clients[1]
        clients = clients[0]

    if type(clients) is list:
        client = clients[0]
    else:
        client = clients
        clients = [clients]

    """ Function removes vlan by name or number from switches """
    falses = False
    log_string = []
    fails_msg = ''
    
    if client.all_path[0] is False:
        return client.all_path

    city = op_define(client.vlan_name)

    print("========================================================================================")
    print("============================ DELETE VLAN ===============================================")
    print(F"All path to switch: {client.all_path}")
    print(f"Vlan name = {client.vlan_name}")
    print(f"Vlan number = {client.vlan_number}")
    print("========================================================================================")
    print("========================================================================================")

    if correct_cl == 'None':
        correct_cl = input('Is the data correct? (y/n): ')

    if correct_cl in "nN":
        print('The program stopped by the user')
        exit()
    elif correct_cl in "yY":
        string_sw = client.all_path
        list_sw = string_sw.split("--")

        for sw_port in list_sw:
            print(sw_port)
            sw_port_edit = sw_port.split("-")
            print("\ntelnet to " + sw_port_edit[1] + " ....")
            try:
                sw_obj = switch.NewSwitch(sw_port_edit[1], login, passw)
            except Exception as e:
                print(f"Не удалось создать объект свитча. \n{kwargs}\n{e}")
            else:
                # #################### START DELETE CLIENTS IN LIST ########################
                for client in clients:
                    answer_code_line = ''
                    save = "save\r"
                    code_line = "delete vlan vl {} \r".format(client.vlan_number)
                    code2_line = "delete vlan {} \r".format(client.vlan_name)

                    response = sw_obj.send_command([code_line, save])
                    answer_code_line += '\n'.join(response if response else ["Error"])

                    if answer_code_line.find("Success") >= 0:

                        print_string = f"=============== {client.vlan_name} TAG {client.vlan_number} === " \
                                       f"SUCCESS removed from {sw_port_edit[1]} ======= by VLAN NUMBER ===== \n"
                        print(print_string)
                    else:
                        response = sw_obj.send_command([code2_line, save])
                        answer_code2_line = '\n'.join(response if response else ["Error"])
                        if answer_code2_line.find("Success") >= 0:
                            print_string = f"=============== {client.vlan_name} TAG {client.vlan_number} " \
                                           f"=== SUCCESS removed from {sw_port_edit[1]} ===== by NAME ======= \n"
                            print(print_string)
                        else:
                            print()
                            print_string = f"========== {client.vlan_name} TAG {client.vlan_number} " \
                                           f"=--= FAIL. NOT removed from {sw_port_edit[1]}.============ \n"
                            print(print_string)
                            falses = True

                    log_string.append(print_string)
                # #################### END DELETE CLIENTS IN LIST ########################

        save_log.create_log(log_string, city, 'delete_vlan')

        if falses:
            for msg in log_string:
                if 'FAIL' in msg:
                    fails_msg += msg
            if que:
                que.put(fails_msg)

            return [False, fails_msg]
        else:
            if que:
                que.put('Delete')

            return [True, "Клиент на свитчах удалён."]

    else:
        print('Data is incorrect! You need type y or n.')
        return [False, 'Data is incorrect! You need type y or n.']


if __name__ == '__main__':
    from work.tools.customers import Customer
    import os

    print(os.path.abspath(os.path.dirname(__file__)))
    state = 'Orel'
    passw = input("passw: ")
    cl_data = [state, '4001', 4000, '172.16.47.122', 15, 'T']
    client = Customer(*cl_data)
    del_code(client, 'y', login='admin', passw=passw)
