# ver 1.0.7
# created by Roman Fedorin
import shelve
from xlrd import open_workbook
# from re import findall
# my
import intranet.full_path_to_sw
import settings


class Customer:
    def __init__(self, state, vname, vnum, switch, sw_port, tag, root_sw=None):

        assert state is not None, "State is not defined!"
        assert vname is not None, "Vlan name is not defined!"
        assert vnum is not None, "Vlan Tag is not defined!"
        assert switch is not None, "Switch is not defined!"
        assert sw_port is not None, "Switch port Tag is not defined!"
        assert tag is not None, "Vlan Tag or Untag is not defined!"

        self.vlan_name = vname
        self.vlan_number = vnum
        self.state = state
        if 'root' in switch:
            _temp = switch.split('root')
            self.switch = _temp[0]
            self.root_sw = _temp[1]
        else:
            self.switch = switch
            self.root_sw = root_sw
        self.sw_port = sw_port
        self.tag = tag

    def get_data_from_intranet(self):
        ip_and_path = dict()
        # ip_pattern = '\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'
        city_shelve = settings.city_shelve

        with shelve.open(city_shelve) as db:

            if self.state in db:
                city_db = db[self.state]
                path_to_intranet = f'{settings.intranet_path}{city_db["city"]}\\'
                intranet = f'{path_to_intranet}Intranet-{city_db["city"]}.xls'
                excel_data_file = open_workbook(intranet)
                root_sw = city_db['root_sw']
                root_port = city_db['root_port']
                col_sw = int(city_db['col_sw'])
            else:
                print("Not found the key of city in db.")
                return [False, False, False]

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

        return ip_and_path, root_port, root_sw

    def get_needed_path(self):
        column_ip, root_port, root_sw = self.get_data_from_intranet()
        if self.root_sw is not None:
            root_sw = self.root_sw
        all_need_path = full_path_to_sw.full_path(self.switch, column_ip, root_port, root_sw, self.state)
        if all_need_path[0] is True:
            return all_need_path[1]
        else:
            return all_need_path

    @property
    def all_path(self):
        return self.get_needed_path()

    def __str__(self):
        return f"""
Instance of class <<Customer>>:

All path         --> {self.all_path}
Customer from OP --> {self.state}
Mnemokod         --> {self.vlan_name}
Vlan             --> {self.vlan_number}
Switch           --> {self.switch}
Port             --> {self.sw_port}
Tag              --> {'Tagged' if self.tag in 'tT' else 'Untagged' if self.tag in 'uU' else 'None'}
        """

