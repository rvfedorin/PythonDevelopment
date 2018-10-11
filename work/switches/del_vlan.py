# ver 1.7.0
# created by Roman Fedorin

# from sys import exit

from full_path_to_sw import login_to_sw
import save_log


def op_define(mnemokod):
    temp = mnemokod.split('-')
    return temp[0]


# string_sw is the full path to the desired switch from the file nodepath
def del_code(clients, correct_cl='y', que=None):

    if isinstance(clients, tuple):
        que = clients[1]
        clients = clients[0]

    if type(clients) is list:
        client = clients[0]
    else:
        client = clients
        clients = [clients]

    """ Function removes vlan by nave or number from switches """
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
            sw_port_edit = sw_port.split("-")
            print("\ntelnet to " + sw_port_edit[1] + " ....")
            tn = login_to_sw(sw_port_edit[1])
            if tn[0] is False:
                msg = f"FAIL. Timeout telnet to {sw_port_edit[1]} \n ERROR \n"
                log_string.append(msg)
                falses = True
                continue
            else:
                tn = tn[1]
            # #################### START DELETE CLIENTS IN LIST ########################
            for client in clients:
                answer_code_line = ''
                code_line = "delete vlan vl {} \r".format(client.vlan_number)
                code2_line = "delete vlan {} \r".format(client.vlan_name)
                tn.write(bytes(code_line, "utf-8"))
                answer_code_line += tn.read_until(b"#", timeout=2).decode()
                answer_code_line += (tn.read_until(b"#", timeout=2)).decode()
                print(answer_code_line)
                if answer_code_line.find("Success") >= 0:

                    print_string = f"=============== {client.vlan_name} TAG {client.vlan_number} === " \
                                   f"SUCCESS removed from {sw_port_edit[1]} ======= by VLAN NUMBER ===== \n"
                    print(print_string)
                else:
                    tn.write(bytes(code2_line, "utf-8"))
                    answer_code2_line = (tn.read_until(b"#", timeout=2)).decode()
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

            tn.write(b"save\r")
            # print((tn.read_until(b"#", timeout=2)).decode())

            tn.write(b"logout\r")

            # raw_date = str(tn.read_very_eager())
            # str_date = raw_date.replace("\\n\\r", "\n")
            # print(str_date)

            tn.close()
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

            return [True]

    else:
        print('Data is incorrect! You need type y or n.')
        return [False]


if __name__ == '__main__':
    from customers import Customer
    state = 'Orel'

    cl_data = [state, '4000', 4000, '172.16.47.122', 15, 'T']
    client = Customer(*cl_data)
    del_code(client, 'y')
