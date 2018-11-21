from PyQt5 import QtWidgets, QtGui, QtCore
from Cryptodome.Cipher import Blowfish
import os

import settings
from tools import work_with_db, customers
from cisco import cisco_class
from switches import switch, create_vlan, del_vlan


class MBContentWindow(QtWidgets.QWidget):
    def __init__(self, parent=None, ico=None):
        super().__init__(parent=parent)
        self.setWindowTitle("Работа с клиентами на Mobibox.")
        self.parent = parent
        # parent.statusBar().showMessage("Ready")

        if ico:
            self.setWindowIcon(ico)
        self.all_fields_full = 0
        self.city = work_with_db.get_list_cities()  # Словарь горд:ключ
        self.city_pref = {v: k for k, v in self.city.items()}  # Словарь префикс:город
        self.key_pass = None
        self.p_un_sup = None
        self.p_sw = None
        self.p_rwr_cl = None
        self.p_rwr_sec = None
        self.my_key = None
        self.my_key_e = None

        self.init_ui()

    def init_ui(self):

        # Блок заголовков и полей ввода строками
        label_mnem = QtWidgets.QLabel("Мнемокод: ")
        label_vlan = QtWidgets.QLabel("Номер влана: ")
        label_ipsw = QtWidgets.QLabel("IP Mobibox: ")
        label_port = QtWidgets.QLabel("Порт: ")

        self.edit_mnem = QtWidgets.QLineEdit()

        self.edit_vlan = QtWidgets.QLineEdit()
        self.edit_vlan.setValidator(QtGui.QIntValidator())

        self.edit_iprwr = QtWidgets.QLineEdit()
        #  валидатор IProotIP
        str_ip = '^((25[0-5]|2[0-4][0-9]|[0-1][0-9]{2}|[0-9]{2}|[0-9])' \
                 '(\.(25[0-5]|2[0-4][0-9]|[0-1][0-9]{2}|[0-9]{2}|[0-9])){3})' \
                 'root' \
                 '((25[0-5]|2[0-4][0-9]|[0-1][0-9]{2}|[0-9]{2}|[0-9])' \
                 '(\.(25[0-5]|2[0-4][0-9]|[0-1][0-9]{2}|[0-9]{2}|[0-9])){3})$;'
        self.regexp_ip = QtCore.QRegExp(str_ip)
        self.edit_iprwr.setValidator(QtGui.QRegExpValidator(self.regexp_ip))

        self.edit_port = QtWidgets.QComboBox()
        self.edit_port.addItems(["ether1", "ether2"])

        self.check_tag = QtWidgets.QCheckBox("Untagged")
        self.check_tag.setStatusTip("По умолчанию tagged")

        self.check_cisco = QtWidgets.QCheckBox("Создать на Cisco")
        self.check_cisco.setStatusTip("Если не выбрать, действие будет выполнено только на свитчах.")

        self.rb_create = QtWidgets.QRadioButton("Создать")
        self.rb_create.setChecked(True)
        self.rb_delete = QtWidgets.QRadioButton("Удалить")
        self.rb_speed = QtWidgets.QRadioButton("Сменить скорость")
        self.rb_speed.setStatusTip("Не забудьте выбрать город, в котором требуется сменить скорость!")

        # Блок кнопок и выбора города
        self.city_list = QtWidgets.QComboBox()
        self.city_list.addItems(sorted(self.city))

        # self.city_list.activated.connect(self.city_choise)
        self.but_free_vlan = QtWidgets.QPushButton(" Найти свободный влан")
        self.but_free_vlan.setStatusTip("Найти свободный интерфейс в выбранном городе.")
        self.but_speed_edit = QtWidgets.QPushButton(" Файл скоростей")
        self.but_speed_edit.setVisible(False)

        # таблица расположения
        # START TABLE
        self.grid_entry = QtWidgets.QGridLayout()
        self.grid_entry.addWidget(label_mnem, 1, 0)
        self.grid_entry.addWidget(self.edit_mnem, 1, 1)
        self.grid_entry.addWidget(self.city_list, 1, 2)

        self.grid_entry.addWidget(label_vlan, 2, 0)
        self.grid_entry.addWidget(self.edit_vlan, 2, 1)
        self.grid_entry.addWidget(self.but_free_vlan, 2, 2)

        self.grid_entry.addWidget(label_ipsw, 3, 0)
        self.grid_entry.addWidget(self.edit_iprwr, 3, 1)

        self.grid_entry.addWidget(label_port, 4, 0)
        self.grid_entry.addWidget(self.edit_port, 4, 1)
        self.grid_entry.setRowMinimumHeight(4, 23)

        self.grid_entry.addWidget(self.check_tag, 5, 1, alignment=QtCore.Qt.AlignTop)

        self.grid_entry.addWidget(self.but_speed_edit, 5, 2)
        self.grid_entry.addWidget(self.check_cisco, 6, 1)

        self.grid_entry.setRowMinimumHeight(6, 25)  # Задаём высоту строки 6
        # END TABLE

        # START GROUP BOX
        self.hbox_radio = QtWidgets.QHBoxLayout()
        self.hbox_radio.addWidget(self.rb_create)
        self.hbox_radio.addWidget(self.rb_delete)
        self.hbox_radio.addWidget(self.rb_speed)
        self.group_box_radio = QtWidgets.QGroupBox("Выберите действие:")
        self.group_box_radio.setLayout(self.hbox_radio)
        # END GROUP BOX

        # кнопка Выплнить
        self.but_run = QtWidgets.QPushButton("&Выполнить")
        self.but_run.setFixedSize(80, 30)
        self.but_run.setDisabled(True)

        # Собираем всё в один бокс
        self.vb = QtWidgets.QVBoxLayout()
        self.vb.addLayout(self.grid_entry)
        self.vb.addWidget(self.group_box_radio)
        self.vb.addSpacing(5)
        self.vb.addWidget(self.but_run, alignment=QtCore.Qt.AlignHCenter)

        self.setLayout(self.vb)

        # добавляем события
        self.but_run.clicked.connect(self.run_b)

        self.edit_mnem.textChanged.connect(self.disable_button)
        self.edit_mnem.textChanged.connect(self.on_city)
        self.edit_vlan.textChanged.connect(self.disable_button)
        self.edit_iprwr.textChanged.connect(self.disable_button)

        self.rb_create.clicked.connect(self.disable_entry)
        self.rb_delete.clicked.connect(self.disable_entry)
        self.rb_speed.clicked.connect(self.disable_entry)

        self.but_free_vlan.clicked.connect(self.get_free_vlan)
        self.but_speed_edit.clicked.connect(self.edit_speed_file)

        # self.show()

    def decrypt_pass(self):
        if self.key_pass:
            try:
                cipher = Blowfish.new(self.key_pass.encode(), Blowfish.MODE_CBC, settings.iv)
                self.p_un_sup = cipher.decrypt(settings.p_un_sup).decode().split('1111')[0]
                cipher = Blowfish.new(self.key_pass.encode(), Blowfish.MODE_CBC, settings.iv)
                self.p_sw = cipher.decrypt(settings.p_sw).decode().split('1111')[0]
                cipher = Blowfish.new(self.key_pass.encode(), Blowfish.MODE_CBC, settings.iv)
                self.p_rwr_cl = cipher.decrypt(settings.p_rwr_cl).decode().split('1111')[0]
                cipher = Blowfish.new(self.key_pass.encode(), Blowfish.MODE_CBC, settings.iv)
                self.p_rwr_sec = cipher.decrypt(settings.p_rwr_sec).decode().split('1111')[0]
                cipher = Blowfish.new(self.key_pass.encode(), Blowfish.MODE_CBC, settings.iv)
                self.my_key = cipher.decrypt(settings.my_key).decode().split('1111')[0]
                cipher = Blowfish.new(self.key_pass.encode(), Blowfish.MODE_CBC, settings.iv)
                self.my_key_e = cipher.decrypt(settings.my_key_e).decode().split('1111')[0]
            except Exception as e:
                print(f"Error while encoded passwords. {e}")
                self.key_pass = None
            finally:
                return True

    def disable_button(self):
        """ Функция включает/отключает кнопки в зависимости от заполнения полей """
        _chek = (len(self.edit_mnem.text())
                 and len(self.edit_vlan.text())
                 and len(self.edit_iprwr.text()))

        # Отключаем кнопку "Выполнить", если не заполнены все поля
        if _chek:
            self.but_run.setDisabled(False)
        else:
            self.but_run.setDisabled(True)

    # Автоматически переключаем на нужный город, если префикс мнемокода совпадает с существующим
    def on_city(self):
        city_try = self.edit_mnem.text().split('-')
        if city_try and city_try[0] in self.city_pref:
            self.city_list.setCurrentText(self.city_pref[city_try[0]])

    # Отключаем поля в завичимости от выбранного действия
    def disable_entry(self):
        """ Функция включает/отключает поля и кнопки,
        в зависимости от выбранного действия [удаление, создание, скорость]"""
        if self.rb_create.isChecked():
            if self.edit_mnem.text() == 'All in file':  # если переходим со вкладки смены скорости
                self.edit_mnem.setText('')
                self.edit_vlan.setText('')
                self.edit_iprwr.setText('')
                self.edit_mnem.setDisabled(False)
                self.edit_vlan.setDisabled(False)
                self.edit_iprwr.setDisabled(False)
                self.but_speed_edit.setVisible(False)
                self.check_cisco.setVisible(True)
            self.check_cisco.setText("Создать на Cisco")
            self.edit_port.setDisabled(False)
            self.check_tag.setDisabled(False)

        elif self.rb_delete.isChecked():
            if self.edit_mnem.text() == 'All in file':  # если переходим со вкладки смены скорости
                self.edit_mnem.setText('')
                self.edit_vlan.setText('')
                self.edit_iprwr.setText('')
                self.edit_mnem.setDisabled(False)
                self.edit_vlan.setDisabled(False)
                self.edit_iprwr.setDisabled(False)
                self.check_tag.setDisabled(False)
                self.but_speed_edit.setVisible(False)
                self.check_cisco.setVisible(True)

            self.check_cisco.setText("Удалить с Cisco")
            self.edit_port.setDisabled(True)
            self.check_tag.setDisabled(True)

        elif self.rb_speed.isChecked():
            self.edit_mnem.setText('All in file')
            self.edit_vlan.setText('4096')
            self.edit_iprwr.setText('255.255.255.255')

            self.edit_mnem.setDisabled(True)
            self.edit_vlan.setDisabled(True)
            self.edit_iprwr.setDisabled(True)
            self.edit_port.setDisabled(True)
            self.check_tag.setDisabled(True)

            self.check_cisco.setVisible(False)
            self.but_speed_edit.setVisible(True)

    @staticmethod
    def edit_speed_file():
        try:
            _path_to_speed = os.path.abspath(os.getcwd() + settings.client_to_change_speed)
            os.startfile(_path_to_speed)
        except:
            print(f"Ошибка открытия файла клиентов со скоростями: {_path_to_speed}")

    def get_free_vlan(self):
        if self.key_pass:
            print("Свободный влан")
            _city = self.city_list.currentText()

            try:
                _cisco = cisco_class.CiscoCreate(self.my_key, self.my_key_e, self.p_un_sup, self.city[_city])
            except Exception as e:
                print(f"Ошибка создания объекта Cisco {e}")
            else:
                try:
                    res = _cisco.get_free_interface()
                except Exception as e:
                    res = f'Error connect to cisco: {_city}; \n{e}'
                else:
                    if not res:
                        res = f'Error connect to cisco: {_city}'
                # print(res)
                _title = f"Свободные интерфейсы на Cisco {_city} " + '_' * 40
                QtWidgets.QInputDialog.getMultiLineText(None,
                                                        "Свободные интерфейсы",
                                                        _title,
                                                        text=res)

    # Запуск действия
    def run_b(self):
        if self.key_pass:
            text = ''
            _cisco_created = False
            _city = self.city_list.currentText()
            if self.check_cisco.isChecked() or self.rb_speed.isChecked():  # Если выбрано создание клиента на cisco
                try:
                    _cisco = cisco_class.CiscoCreate(self.my_key, self.my_key_e, self.p_un_sup, self.city[_city])
                except Exception as e:
                    text = f"Ошибка создания объекта cisco.\n main.py:ContentWindow:run_b\n{e}"
                    print(text)
                    QtWidgets.QMessageBox.information(None,
                                                      "Выполнение",
                                                      text)
                else:
                    _cisco_created = True

            state_pref = self.city[_city]
            mnemo = self.edit_mnem.text()
            vl_number = self.edit_vlan.text()
            switch = self.edit_iprwr.text()
            port = self.edit_port.currentText()
            taguntag = 'U' if self.check_tag.isChecked() else 'T'
            root_sw_other = None

            if 'root' in switch:  # если надо сделать другой свитч корневым
                switch, root_sw_other = switch.split('root')

            _all_data_list = [
                state_pref,
                mnemo,
                vl_number,
                switch,
                port,
                taguntag,
            ]

            print(f'Creating instance client {mnemo}... ')
            _client = customers.Customer(*_all_data_list, root_sw_other)

            # Блок выбора действия
            if self.rb_create.isChecked():  #
                print("Идёт создание клиента на rwr и свитчах")
                self.parent.statusBar().showMessage("Идёт создание клиента на rwr и свитчах")
                # ########### RWR BLOCK START ############
                # ########### RWR BLOCK END ############
                res = create_vlan.create_vlan(_client, 'y', 'admin', self.p_sw)  # return [True, _message]

                if len(res[1]) > 0 and res[0]:
                    text += f'\n{res[1]}'
                elif res[0]:
                    text += 'Клиент на свитчах создан.\n'
                else:
                    text += '[!!!] Ошибка создания клиента на свитчах.\n'

                if _cisco_created:  # ###################### СОЗДАНИЕ
                    print("Идёт создание клиента на cisco")
                    self.parent.statusBar().showMessage("Идёт создание клиента на cisco")
                    result_create = _cisco.create_on_cisco(_client)
                    if len(result_create) > 1 and not result_create[0]:
                        res[0] = False
                        text += f'{res[1]}\n\nERROR CREATE ON CISCO!!!\n{result_create[1]}'
                    elif not result_create[0]:
                        res[0] = False
                        text += f'\n\nERROR CREATE ON CISCO!!!\nMaybe NOT FOUND'
                    else:
                        text += "\nКлиент на cisco создан.\n"

            elif self.rb_delete.isChecked():  # ###################### УДАЛЕНИЕ
                self.parent.statusBar().showMessage("Идёт удаление клиента на свитчах")
                res = del_vlan.del_code(clients=_client, correct_cl='y', passw=self.p_sw)  # return list

                if len(res[1]) > 0 and res[0]:
                    text += f'\n{res[1]}'
                elif len(res[1]) > 0:
                    text += f'Возникли ошибки при удалении на свитчах.\n {res[1]}'

                if _cisco_created:  # если создан объект циски
                    self.parent.statusBar().showMessage("Идёт удаление клиента на cisco")
                    result_delete = _cisco.delete_from_cisco([_client])  # [False, clients_not_found] or if allgood [log]
                    if result_delete[0]:
                        text += "\nКлиент на cisco удалён.\n"
                    else:
                        text += f"\nОшибка удаления клиента на cisco.\n {result_delete[1]}\n"

            elif self.rb_speed.isChecked():   # ###################### СКОРОСТЬ
                print("Смена скорости.")
                _changed = ''
                _not_changed = ''
                res = _cisco.change_speed()  # return [True, clients_not_done, clients_not_found]
                print(222)
                if len(res[1]) > 0:
                    for cust_speed in res[1]:
                        _changed += f'\nSuccess: {cust_speed}'

                if len(res[2]) > 0:
                    for cust_speed in res[2]:
                        _not_changed += f'\n Not changed: {cust_speed}\n'

                text = f'\n{_changed} \n {_not_changed}\n'

            self.parent.statusBar().showMessage("Ready")
            _title = f"Результат выполнения: " + '_' * 80
            QtWidgets.QInputDialog.getMultiLineText(None,
                                                    "Выполнение",
                                                    _title,
                                                    text=text)
        else:   # if self.key_pass:
            text = 'Невозможно выполнять действие без верного ключа.'
            QtWidgets.QMessageBox.information(None,
                                              "Выполнение",
                                              text)