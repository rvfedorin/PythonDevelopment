from PyQt5 import QtWidgets, QtGui, QtCore
import sys
import os
import shelve
from Cryptodome.Cipher import Blowfish

from work import settings
from work.tools import work_with_db
from work.cisco import create_cl_cisco
from work.switches import switch


def get_list_cities():
    """ Function reads all keys of cities from shelveDB """
    city_shelve = os.path.abspath(os.getcwd() + settings.city_shelve)
    print(city_shelve)
    cities_keys = {}
    with shelve.open(city_shelve) as db:
        for key in db:
            cities_keys[db[key]['city']] = key
    return cities_keys


class MainWindow(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.all_fields_full = 0
        self.city = work_with_db.get_list_cities()  # Словарь горд:ключ
        self.city_pref = {v: k for k, v in self.city.items()}  # Словарь ключ:город
        self.key_pass = None
        self.p_un_sup = None
        self.p_sw = None
        self.my_key = None
        self.my_key_e = None

        # Блок заголовков и полей ввода строками
        label_mnem = QtWidgets.QLabel("Мнемокод: ")
        label_vlan = QtWidgets.QLabel("Номер влана: ")
        label_ipsw = QtWidgets.QLabel("IP свитча: ")
        label_port = QtWidgets.QLabel("Порт: ")

        self.edit_mnem = QtWidgets.QLineEdit()

        self.edit_vlan = QtWidgets.QLineEdit()
        self.edit_vlan.setValidator(QtGui.QIntValidator())

        self.edit_ipsw = QtWidgets.QLineEdit()
        str_ip = '^((25[0-5]|2[0-4][0-9]|[0-1][0-9]{2}|[0-9]{2}|[0-9])' \
                 '(\.(25[0-5]|2[0-4][0-9]|[0-1][0-9]{2}|[0-9]{2}|[0-9])){3})$;'
        regexp_ip = QtCore.QRegExp(str_ip)
        self.edit_ipsw.setValidator(QtGui.QRegExpValidator(regexp_ip))

        self.edit_port = QtWidgets.QLineEdit()
        self.edit_port.setValidator(QtGui.QIntValidator())

        self.check_tag = QtWidgets.QCheckBox("Untagged")
        self.check_tag.setToolTip("По умолчанию tagged")

        self.check_cisco = QtWidgets.QCheckBox("Создать на Cisco")

        self.rb_create = QtWidgets.QRadioButton("Создать")
        self.rb_create.setChecked(True)
        self.rb_delete = QtWidgets.QRadioButton("Удалить")
        self.rb_speed = QtWidgets.QRadioButton("Сменить скорость")

        # Блок кнопок и выбора города
        self.city_list = QtWidgets.QComboBox()
        self.city_list.addItems(sorted(self.city))

        # self.city_list.activated.connect(self.city_choise)
        self.but_free_vlan = QtWidgets.QPushButton(" Найти свободный влан")
        self.but_free_port = QtWidgets.QPushButton(" Найти свободный порт")
        self.but_free_port.setToolTip("Необходимо, чтобы был указан IP свитча")
        self.but_free_port.setDisabled(True)
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
        self.grid_entry.addWidget(self.edit_ipsw, 3, 1)

        self.grid_entry.addWidget(label_port, 4, 0)
        self.grid_entry.addWidget(self.edit_port, 4, 1)
        self.grid_entry.addWidget(self.but_free_port, 4, 2)

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
        self.edit_ipsw.textChanged.connect(self.disable_button)
        self.edit_port.textChanged.connect(self.disable_button)

        self.rb_create.clicked.connect(self.disable_entry)
        self.rb_delete.clicked.connect(self.disable_entry)
        self.rb_speed.clicked.connect(self.disable_entry)

        self.but_free_vlan.clicked.connect(self.get_free_vlan)
        self.but_free_port.clicked.connect(self.get_free_port)
        self.but_speed_edit.clicked.connect(self.edit_speed_file)

    def decrypt_pass(self):
        if self.key_pass:
            try:
                cipher = Blowfish.new(self.key_pass.encode(), Blowfish.MODE_CBC, settings.iv)
                self.p_un_sup = cipher.decrypt(settings.p_un_sup).decode().split('1111')[0]
                cipher = Blowfish.new(self.key_pass.encode(), Blowfish.MODE_CBC, settings.iv)
                self.p_sw = cipher.decrypt(settings.p_sw).decode().split('1111')[0]
                cipher = Blowfish.new(self.key_pass.encode(), Blowfish.MODE_CBC, settings.iv)
                self.my_key = cipher.decrypt(settings.my_key).decode().split('1111')[0]
                cipher = Blowfish.new(self.key_pass.encode(), Blowfish.MODE_CBC, settings.iv)
                self.my_key_e = cipher.decrypt(settings.my_key_e).decode().split('1111')[0]
            except:
                self.key_pass = None
            finally:
                return True

    def disable_button(self):
        """ Функция включает/отключает кнопки в зависимости от заполнения полей """
        _chek = (len(self.edit_mnem.text())
                 and len(self.edit_vlan.text())
                 and len(self.edit_ipsw.text())
                 and len(self.edit_port.text()))
        # Отключаем кнопку "Выполнить", если не заполнены все поля
        if _chek:
            self.but_run.setDisabled(False)
        else:
            self.but_run.setDisabled(True)

        # включение/отключение кнопки свободного порта
        if self.edit_ipsw.text().count('.') == 3:
            self.but_free_port.setDisabled(False)
        else:
            self.but_free_port.setDisabled(True)

    # Автоматически переключаем на нужный город, если префикс мнемокода совпадает с существующим
    def on_city(self):
        city_try = self.edit_mnem.text().split('-')
        if city_try and city_try[0] in self.city_pref:
            self.city_list.setCurrentText(self.city_pref[city_try[0]])

    # Отключаем поля в завичимости от выбранного действия
    def disable_entry(self):
        """ Функция включает/отключает поля, в зависимости от выбранного действия [удаление, создание, скорость]"""
        if self.rb_create.isChecked():
            if self.edit_mnem.text() == 'All in file':  # если переходим со вкладки смены скорости
                self.edit_mnem.setText('')
                self.edit_vlan.setText('')
                self.edit_ipsw.setText('')
                self.edit_mnem.setDisabled(False)
                self.edit_vlan.setDisabled(False)
                self.edit_ipsw.setDisabled(False)
                self.but_speed_edit.setVisible(False)
                self.check_cisco.setVisible(True)
                self.check_tag.setDisabled(False)
            self.edit_port.setText('')
            self.check_cisco.setText("Создать на Cisco")
            self.edit_port.setDisabled(False)

        elif self.rb_delete.isChecked():
            if self.edit_mnem.text() == 'All in file':  # если переходим со вкладки смены скорости
                self.edit_mnem.setText('')
                self.edit_vlan.setText('')
                self.edit_ipsw.setText('')
                self.edit_mnem.setDisabled(False)
                self.edit_vlan.setDisabled(False)
                self.edit_ipsw.setDisabled(False)
                self.check_tag.setDisabled(False)
                self.but_speed_edit.setVisible(False)
                self.check_cisco.setVisible(True)

            self.check_cisco.setText("Удалить с Cisco")
            self.edit_port.setText('999')
            self.edit_port.setDisabled(True)

        elif self.rb_speed.isChecked():
            self.edit_mnem.setText('All in file')
            self.edit_vlan.setText('4096')
            self.edit_ipsw.setText('255.255.255.255')
            self.edit_port.setText('999')

            self.edit_mnem.setDisabled(True)
            self.edit_vlan.setDisabled(True)
            self.edit_ipsw.setDisabled(True)
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
            print(_city)
            # print(self.my_key, self.my_key_e, self.p_un_sup, self.city[_city])
            try:
                _cisco = create_cl_cisco.CiscoCreate(self.my_key, self.my_key_e, self.p_un_sup, self.city[_city])
            except Exception as e:
                print(f"Ошибка создания интерфейса Cisco {e}")
            else:
                res = _cisco.get_free_interface()
                if not res:
                    res = f'Error connect to cisco: {_city}'
                # print(res)
                QtWidgets.QInputDialog.getMultiLineText(None,
                                                        "Свободные интерфейсы",
                                                        f"Свободные интерфейсы на Cisco {_city}",
                                                        text=res)

    def get_free_port(self):
        if self.key_pass:
            print("Свободный порт")
            _sw = switch.NewSwitch(self.edit_ipsw.text(), sw_passw=self.p_sw)
            res = '\n'.join(_sw.find_free_port())
            print(f'{res}')
            QtWidgets.QInputDialog.getMultiLineText(None,
                                                    "Свободные порты",
                                                    f"Свободные порты на свитче {self.edit_ipsw.text()}",
                                                    text=res)

    # Запуск действия
    def run_b(self):
        print(self.city_list.currentText())
        print(self.edit_mnem.text())
        print(self.edit_vlan.text())
        print(self.edit_ipsw.text())
        print(self.edit_port.text())
        print(self.check_tag.isChecked())
        print(self.rb_create.isChecked())
        print(self.rb_delete.isChecked())
        print(self.rb_speed.isChecked())


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    ico = QtGui.QIcon("ico.jpg")
    window = MainWindow()
    window.setWindowTitle("Работа с клиентами.")
    window.resize(400, 200)
    window.setWindowIcon(ico)

    # Запрос ключа для рассшифровки паролей
    dialog_pass = QtWidgets.QInputDialog()
    dialog_pass.setWindowTitle("Ключ для работы с устройствами.")
    dialog_pass.setLabelText("Введите ключ, для разблокировки паролей:")
    dialog_pass.setTextEchoMode(QtWidgets.QLineEdit.Password)
    get_pass = dialog_pass.exec()
    if get_pass == QtWidgets.QDialog.Accepted:
        window.key_pass = dialog_pass.textValue()
        window.decrypt_pass()

    window.show()

    sys.exit(app.exec_())
