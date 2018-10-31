# ver 1.0.2
# created by Roman Fedorin
import shelve
from xlrd import open_workbook
from re import findall
from collections import deque
# my
from work import settings


def get_graph_neighbors(op, sw):
    _op, _sw = op, sw
    graph_neighbors = dict()
    que = deque([_sw + ' '])
    ip_pattern = '\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'
    city_shelve = settings.city_shelve

    with shelve.open(city_shelve) as db:

        if _op in db:
            city_db = db[_op]
            path_to_intranet = f'{settings.intranet_path}{city_db["city"]}\\'
            intranet = f'{path_to_intranet}Intranet-{city_db["city"]}.xls'
            excel_data_file = open_workbook(intranet)
            col_sw = int(city_db['col_sw'])
        else:
            message = "Not found the key of city in db or file."
            print(message)
            return False, message

    sheet = excel_data_file.sheet_by_index(0)
    row_number = sheet.nrows

    if row_number > 0:

        while que:
            current_sw = que.popleft()
            for row in range(0, row_number):
                neighbor = len(findall(current_sw, str(sheet.row_values(row)[col_sw + 1])))
                if neighbor:
                    ip_neighor = str(sheet.row_values(row)[col_sw])
                    if ip_neighor and findall(ip_pattern, ip_neighor):
                        if current_sw in graph_neighbors:
                            graph_neighbors[current_sw].add(ip_neighor)
                            que.append(ip_neighor + ' ')
                        else:
                            graph_neighbors[current_sw] = set()
                            graph_neighbors[current_sw].add(ip_neighor)
                            que.append(ip_neighor + ' ')
    else:
        print("Excel файл с данными пустой или заполнен не верно")

    return graph_neighbors


def get_clients_from_intranet(state, switch):  # ip + path (via port 1 sw 11111 to port)
    clients = ''
    success = False
    befor = 0
    _len = len(state)
    city_shelve = settings.city_shelve

    with shelve.open(city_shelve) as db:

        if state in db:
            city_db = db[state]
            path_to_intranet = f'{settings.intranet_path}{city_db["city"]}\\'
            intranet = f'{path_to_intranet}Intranet-{city_db["city"]}.xls'
            excel_data_file = open_workbook(intranet)
            col_sw = int(city_db['col_sw'])
        else:
            print(f"Not found the key='{state}' of city in db. (gui_main.py/get_data_from_intranet)")
            return [False, False]

    sheet = excel_data_file.sheet_by_index(0)
    row_number = sheet.nrows

    if row_number > 0:
        for row in range(0, row_number):
            column_ip = str(sheet.row_values(row)[col_sw]).strip()

            if success:
                clients_mnemo = str(sheet.row_values(row)[0])
                if not clients_mnemo:
                    befor += 1
                    continue
                elif clients_mnemo[0:_len] == state or clients_mnemo[0:_len+3] == f'TDM{state}':
                    clients += f'    {clients_mnemo}\n'
                    befor = 0
                elif befor > 1:
                    return clients
                else:
                    befor += 1
            elif switch == column_ip:
                success = True

    else:
        print("Excel файл с данными пустой или заполнен не верно")


if __name__ == '__main__':
    from pprint import pprint
    op, sw = 'Orel', '172.16.48.146'
    gr = get_graph_neighbors(op, sw)
    # pprint(gr)
    for key in gr:
        for sw in gr[key]:
            print(sw)