import shelve
from xlrd import open_workbook
from work import settings


def get_data_from_intranet(state):  # ip + path (via port 1 sw 11111 to port)
    ip_and_path = dict()
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
            stolbec_ip_up = str(sheet.row_values(row)[col_sw + 1])
            if not column_ip and not stolbec_ip_up:
                continue
            ip_and_path[column_ip] = stolbec_ip_up
    else:
        print("Excel файл с данными пустой или заполнен не верно")

    return ip_and_path


if __name__ == '__main__':
    print(get_data_from_intranet('Orel'))