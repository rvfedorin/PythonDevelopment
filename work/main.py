from PyQt5 import QtWidgets, QtGui, QtCore
import sys
import os
import shelve
from functools import partial
from multiprocessing import Pool, Manager
from time import sleep

import settings
from tools import work_with_db, customers
from cisco import cisco_class
from switches import switch, create_vlan, del_vlan
from intranet import full_path_to_sw, tools, all_neighbor
from dectypt import DecryptPass

from mobibox import mobibox_gui


def get_list_cities():
    """ Function reads all keys of cities from shelveDB """
    city_shelve = os.path.abspath(os.getcwd() + settings.city_shelve)
    cities_keys = {}
    with shelve.open(city_shelve) as db:
        for key in db:
            cities_keys[db[key]['city']] = key
    return cities_keys


class PathSwThread(QtCore.QThread):
    mysignal = QtCore.pyqtSignal(str)

    def __init__(self, ended_switch, column_ip, root_port, root_sw, city, only_path, p_sw):
        super(PathSwThread, self).__init__()
        self.ended_switch = ended_switch
        self.column_ip = column_ip
        self.root_port = root_port
        self.root_sw = root_sw
        self.city = city
        self.p_sw = p_sw
        self.only_path = only_path

    def run(self):
        try:
            _path_to_sw = full_path_to_sw.full_path(self.ended_switch,
                                                    self.column_ip,
                                                    self.root_port,
                                                    self.root_sw,
                                                    self.city)
        except Exception as e:
            print(e)
        else:
            if _path_to_sw[0]:
                try:
                    if not self.only_path:
                        _path_with_links = full_path_to_sw.type_connection(_path_to_sw[1], _passw=self.p_sw)
                        _path_to_sw = _path_with_links

                except Exception as e:
                    self.mysignal.emit(
                        f"Путь до свитча {self.ended_switch}XXXОшибка подключения: {e}\nПуть:{_path_to_sw}")
                    print(e)
                else:
                    self.mysignal.emit(f"Путь до свитча {self.ended_switch}XXX{_path_to_sw[1]}")


class CreateMulVlanThread(QtCore.QThread):
    mysignal = QtCore.pyqtSignal(str)

    def __init__(self, clients, p_sw):
        super(CreateMulVlanThread, self).__init__()
        self.clients = clients[:]
        self.p_sw = p_sw

    def run(self):
        try:
            res = create_vlan.create_vlan(self.clients, 'y', 'admin', self.p_sw)
        except Exception as e:
            print(e)
        else:
            # XXX разделитель заголовка и тела сообщения
            self.mysignal.emit(f"Создание вланов по списку XXXСделано.\n{res[1]}")


class DelMulVlanThread(QtCore.QThread):
    mysignal = QtCore.pyqtSignal(str)

    def __init__(self, clients, p_sw):
        super(DelMulVlanThread, self).__init__()
        self.clients = clients[:]
        self.p_sw = p_sw
        self._manager = Manager()
        self._queue = self._manager.Queue()

    def run(self):
        kwarg = {'que': self._queue, 'passw': self.p_sw}
        try:
            with Pool(8) as p:
                p.map(partial(del_vlan.del_code, **kwarg), self.clients)

            res = self._queue.get()
        except Exception as e:
            _t = f"Ошибка удаления main.py:DelMulVlanThread: {e}"
            print(_t)
            self.mysignal.emit(f"Удаление вланов по списку XXX{_t}\n")
        else:
            # XXX разделитель заголовка и тела сообщения
            self.mysignal.emit(f"Удаление вланов по списку XXXСделано.\n{res}")


class WorkWithDB(QtWidgets.QWidget):
    def __init__(self, window, parent=None):
        super().__init__(parent, QtCore.Qt.Window)
        self.setMinimumWidth(450)
        ico = QtGui.QIcon(settings.ico)
        self.setWindowIcon(ico)
        self.setWindowTitle("Работа с базой данных.")
        self.cities = get_list_cities()  # город:префикс
        self.content_window = window
        self.build()

    @property
    def cities_revers(self):
        return {v: k for k, v in self.cities.items()}

    def build(self):
        self.form = QtWidgets.QFormLayout(self)

        self.cities_list = QtWidgets.QComboBox()
        self.cities_list.addItems(sorted(self.cities))
        self.cities_list.activated.connect(self.get_data)

        self.prefix_entry = QtWidgets.QLineEdit()
        self.city_entry = QtWidgets.QLineEdit()
        self.root_sw_entry = QtWidgets.QLineEdit()
        self.root_port_entry = QtWidgets.QLineEdit()
        self.col_sw_entry = QtWidgets.QLineEdit()
        self.unix_entry = QtWidgets.QLineEdit()
        self.mobi_entry = QtWidgets.QLineEdit()

        # START GROUP BOX
        self.rb_create = QtWidgets.QRadioButton("Создать")
        self.rb_create.setChecked(True)
        self.rb_update = QtWidgets.QRadioButton("Обновить")
        self.rb_delete = QtWidgets.QRadioButton("Удалить")

        self.hbox_radio = QtWidgets.QHBoxLayout()
        self.hbox_radio.addWidget(self.rb_create)
        self.hbox_radio.addWidget(self.rb_update)
        self.hbox_radio.addWidget(self.rb_delete)
        self.group_box_radio = QtWidgets.QGroupBox("Выберите действие:")
        self.group_box_radio.setLayout(self.hbox_radio)
        # END GROUP BOX

        self.but_run = QtWidgets.QPushButton(" Выполнить ")
        # self.but_run.setStyleSheet("""
        #     QPushButton:hover { background-color: red }
        #     QPushButton:!hover { background-color: white }
        #
        #     QPushButton:pressed { background-color: rgb(0, 255, 0); }
        # """)
        self.but_run.clicked.connect(self.run_data)
        self.but_quit = QtWidgets.QPushButton("Закрыть")
        self.but_quit.clicked.connect(self.close)

        self.form.addRow(self.cities_list)
        self.form.addRow("Префикс мнемокода: ", self.prefix_entry)
        self.form.addRow("Город: ", self.city_entry)
        self.form.addRow("Корневой свитч: ", self.root_sw_entry)
        self.form.addRow("Порт подключения cisco: ", self.root_port_entry)
        self.form.addRow("Колонка с IP свитчей: ", self.col_sw_entry)
        self.form.addRow("Unix: ", self.unix_entry)
        self.form.addRow("Mobibox: ", self.mobi_entry)
        self.form.addRow(self.group_box_radio)
        self.form.addRow(self.but_run, self.but_quit)

    def get_data(self, event):
        _city = self.cities_list.currentText()
        if _city:
            _key = self.cities[_city]
            res = work_with_db.get_data_from_db(_key)

            if res is not None:
                self.prefix_entry.setText(_key)
                self.city_entry.setText(res['city'])
                self.root_sw_entry.setText(res['root_sw'])
                self.root_port_entry.setText(res['root_port'])
                self.col_sw_entry.setText(str(res['col_sw']))
                self.unix_entry.setText(res['unix'])
                self.mobi_entry.setText(res['Mobibox'])
        else:
            text = 'Вам необходимо указать префикс или выбрать город из списка.'
            QtWidgets.QMessageBox.information(None,
                                        "База данных",
                                        text)

    def run_data(self, event):
        all_field = (self.prefix_entry.text()
                     and self.city_entry.text()
                     and self.root_sw_entry.text()
                     and self.root_port_entry.text()
                     and self.col_sw_entry.text()
                     and self.unix_entry.text()
                     and self.mobi_entry.text())

        if all_field:
            if self.rb_create.isChecked():  # Создание записи
                if self.prefix_entry.text() in self.cities_revers or self.city_entry.text() in self.cities:
                    text = 'Такой префикс или город уже существует.'
                    QtWidgets.QMessageBox.information(None,
                                                      "База данных",
                                                      text)
                else:
                    _key = self.prefix_entry.text()
                    _city = self.city_entry.text()
                    _sw = self.root_sw_entry.text()
                    _port = self.root_port_entry.text()
                    _col = self.col_sw_entry.text()
                    _unix = self.unix_entry.text()
                    _mobi = self.mobi_entry.text()

                    try:
                        _dict = {'city': _city,
                                 'root_sw': _sw,
                                 'root_port': _port,
                                 'col_sw': _col,
                                 'unix': _unix,
                                 'Mobibox': _mobi}

                        city_shelve = settings.city_shelve
                        with shelve.open(city_shelve) as db:
                            work_with_db.add_to_db(db, _key, _dict)
                        self.cities_list.clear()
                        self.cities.clear()
                        self.cities.update(get_list_cities())
                        self.cities_list.addItems(sorted(self.cities))

                        # обновляем и в главном окне
                        self.content_window.city.clear()
                        self.content_window.city.update(get_list_cities())
                        self.content_window.city_list.clear()
                        self.content_window.city_list.addItems(sorted(self.cities))

                    except Exception as e:
                        text = f"Ошибка добавления. {e}"
                    else:
                        text = f'Запись {_key} добавлена.'

                    QtWidgets.QMessageBox.information(None,
                                                      "База данных",
                                                      text)
            elif self.rb_update.isChecked():  # Изменения в существующей записи
                _key = self.prefix_entry.text()
                _city = self.city_entry.text()
                _sw = self.root_sw_entry.text()
                _port = self.root_port_entry.text()
                _col = self.col_sw_entry.text()
                _unix = self.unix_entry.text()
                _mobi = self.mobi_entry.text()

                _dict = {'city': _city,
                         'root_sw': _sw,
                         'root_port': _port,
                         'col_sw': _col,
                         'unix': _unix,
                         'Mobibox': _mobi}
                try:
                    city_shelve = settings.city_shelve
                    print(_dict)
                    with shelve.open(city_shelve) as db:
                        work_with_db.update_in_db(db, _key, _dict)
                except Exception as e:
                    text = f'Ошибка изменения записи. \n Префикс изменить нельзя, необходимо пересоздавать. {e}'
                else:
                    self.cities_list.clear()
                    self.cities.clear()
                    self.cities.update(get_list_cities())
                    self.cities_list.addItems(sorted(self.cities))

                    # обновляем и в главном окне
                    self.content_window.city.clear()
                    self.content_window.city.update(get_list_cities())
                    self.content_window.city_list.clear()
                    self.content_window.city_list.addItems(sorted(self.cities))

                    text = f'Запись {_key} успешно изменена.'

                QtWidgets.QMessageBox.information(None,
                                                  "База данных",
                                                  text)

            elif self.rb_delete.isChecked():  # Удаление записи
                text = ''
                _key = self.prefix_entry.text()
                try:
                    res = QtWidgets.QMessageBox.question(None,
                                                         "База данных.",
                                                         "Вы действительно хотите удалить запись?",
                                                         buttons=QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.No)
                    if res == QtWidgets.QMessageBox.Ok:
                        city_shelve = settings.city_shelve
                        with shelve.open(city_shelve) as db:
                            work_with_db.delete_from_db(db, _key)
                            text = f'Запись {_key} успешно удалена.'
                except Exception as e:
                    text = f'Ошибка удаления записи. {e}'
                else:
                    self.cities_list.clear()
                    self.cities.clear()
                    self.cities.update(get_list_cities())
                    self.cities_list.addItems(sorted(self.cities))

                    # обновляем и в главном окне
                    self.content_window.city.clear()
                    self.content_window.city.update(get_list_cities())
                    self.content_window.city_list.clear()
                    self.content_window.city_list.addItems(sorted(self.cities))

                if text:
                    QtWidgets.QMessageBox.information(None,
                                                  "База данных",
                                                  text)

        else:  # if all_field:
            text = 'Необходимо заполнить все поля.'
            QtWidgets.QMessageBox.information(None,
                                              "База данных",
                                              text)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.resize(410, 300)  # x, y
        self.setWindowTitle("Работа с клиентами.")
        self.window_optic = OpticContentWindow(self)
        self.window_rwr = RwrContentWindow(self)
        self.window_mb = mobibox_gui.MBContentWindow(self)
        self.content_tab = QtWidgets.QTabWidget()
        self.action = True
        self.init_ui()

    def init_ui(self):
        self.statusBar().showMessage("Ready")
        main_menu = self.menuBar()

        # self.setCentralWidget(self.window)
        self.content_tab.addTab(self.window_optic, "&Optic")
        self.content_tab.addTab(self.window_mb, "&Mobibox")
        self.content_tab.addTab(self.window_rwr, "&Rwr")
        self.setCentralWidget(self.content_tab)

        # МЕНЮ
        menu_tools = main_menu.addMenu('Tools')
        menu_tools.menuAction().setStatusTip("Работа с БД; Массовое Создание/Удаление vlan")
        menu_tools_db = menu_tools.addAction("Работа с БД")
        menu_tools_db.triggered.connect(self.work_db)
        menu_tools_cml = menu_tools.addAction("Массовое создание vlan")
        menu_tools_cml.triggered.connect(self.crea_mv)
        menu_tools_dml = menu_tools.addAction("Массовое удаление vlan")
        menu_tools_dml.triggered.connect(self.dele_mv)

        menu_switch = main_menu.addMenu('Switch')
        menu_switch.menuAction().setStatusTip("Путь до свитча; Все подключения от свитча")
        menu_switch_path = menu_switch.addAction("Путь до свитча")
        menu_switch_path.triggered.connect(self.path_sw_runner)
        menu_switch_connected = menu_switch.addAction("Все подключения от свитча")
        menu_switch_connected.triggered.connect(self.connected_sw)

        menu_help = main_menu.addMenu('Help')
        menu_help.menuAction().setStatusTip("Help; About")
        menu_help_manual = menu_help.addAction("Manual")
        menu_help_manual.triggered.connect(self.help)
        menu_help_about = menu_help.addAction("About")
        menu_help_about.triggered.connect(self.about)
        # МЕНЮ

    @staticmethod
    def about():
        QtWidgets.QMessageBox.about(None,
                                    "О программе",
                                    "Version 1.1.3\nPowered by Roman Fedorin")

    @staticmethod
    def help():
        _path = os.path.abspath(os.getcwd() + settings.help_file)

        try:
            with open(_path, 'r') as f:
                text = ''.join(f.readlines())
        except Exception as e:
            print(f"Ошибка открытия файла с мануалом. {e}")
        else:
            QtWidgets.QMessageBox.about(None,
                                        "Инструкция",
                                        text)

    def path_sw_runner(self):
        self.statusBar().showMessage("Идёт поиск пути до свитча ...")
        # Окно запроса начало
        _win = QtWidgets.QDialog()
        _win.setWindowTitle("Поиск цепочки подключения свитча.")
        _form = QtWidgets.QFormLayout()

        _city_list = QtWidgets.QComboBox()
        _city_list.addItems(sorted(self.window_optic.city))
        _city_list.setCurrentText(self.window_optic.city_list.currentText())
        _sw_ent = QtWidgets.QLineEdit()
        _sw_ent.setValidator(QtGui.QRegExpValidator(self.window_optic.regexp_ip))
        _check_only_path = QtWidgets.QCheckBox("Показать путь без линков.")

        _but_ok = QtWidgets.QPushButton("Ok")
        _but_ok.clicked.connect(_win.accept)
        _but_cancel = QtWidgets.QPushButton("Cancel")
        _but_cancel.clicked.connect(_win.reject)

        _form.addRow(_city_list)
        _form.addRow("IP свитча: ", _sw_ent)
        _form.addRow(_check_only_path)
        _form.addRow(_but_ok, _but_cancel)

        _win.setLayout(_form)
        # Окно запроса конец

        result = _win.exec()
        if result and _sw_ent.text():
            _city = _city_list.currentText()
            _key = self.window_optic.city[_city]

            # Пробуем вытянуть данные из базы по городу
            try:
                city_db = work_with_db.get_data_from_db(_key)
            except Exception as e:
                print(f"Ошибка доступа к базе. {e}")
                raise Exception("Ошибка доступа к базе. {e}")

            if city_db is not None:
                ended_switch = _sw_ent.text()
                city = str(city_db['city']).strip()
                root_port = str(city_db['root_port']).strip()
                root_sw = str(city_db['root_sw']).strip()
                only_path = _check_only_path.isChecked()

                # Пробуем получить данные из интранета
                try:
                    column_ip = tools.get_data_from_intranet(_key)
                except Exception as e:
                    print(f"Ошибка поиска в интранете. {e}")
                else:
                    self._thread = PathSwThread(ended_switch,
                                                column_ip,
                                                root_port,
                                                root_sw,
                                                city,
                                                only_path,
                                                self.window_optic.p_sw)
                    self._thread.mysignal.connect(self.message_out)
                    self._thread.start()

                    self.work_in_progress()


        else:
            self.statusBar().showMessage("Ready")

    def message_out(self, value):
        self.statusBar().showMessage("Ready")
        if value:
            _title, _body = value.split('XXX')
            _title += "_" * 80
            win_name = _title

            QtWidgets.QInputDialog.getMultiLineText(None,
                                                    win_name,
                                                    _title,
                                                    text=_body)

    def work_in_progress(self):
        count = 1
        while self._thread.isRunning():
            sleep(1)
            _text = "." * count
            self.statusBar().showMessage(_text)
            if count > 25:
                count = 1
            else:
                count += 1

    def connected_sw(self):
        # Окно запроса начало
        _win = QtWidgets.QDialog()
        _win.setWindowTitle("Поиск цепочки подключения свитча.")
        _form = QtWidgets.QFormLayout()

        _city_list = QtWidgets.QComboBox()
        _city_list.addItems(sorted(self.window_optic.city))
        _city_list.setCurrentText(self.window_optic.city_list.currentText())
        _sw_ent = QtWidgets.QLineEdit()
        _sw_ent.setValidator(QtGui.QRegExpValidator(self.window_optic.regexp_ip))
        _check_short = QtWidgets.QCheckBox("Показать только свитчи")

        _but_ok = QtWidgets.QPushButton("Ok")
        _but_ok.clicked.connect(_win.accept)
        _but_cancel = QtWidgets.QPushButton("Cancel")
        _but_cancel.clicked.connect(_win.reject)

        _form.addRow(_city_list)
        _form.addRow("IP свитча: ", _sw_ent)
        _form.addRow(_check_short)
        _form.addRow(_but_ok, _but_cancel)

        _win.setLayout(_form)
        # Окно запроса конец

        result = _win.exec()

        if result and _sw_ent.text():
            _city = _city_list.currentText()
            _key = self.window_optic.city[_city]
            _ip = _sw_ent.text()
            with_clients = not _check_short.isChecked()
            row = _default = 4
            text = ''

            #           свитч              его соседи
            #  out: {'172.17.127.142 ': {'172.17.152.222', '172.17.124.242 '}}
            neighbors = all_neighbor.get_graph_neighbors(_key, _ip)

            if with_clients:
                text += f'{_ip}\n{all_neighbor.get_clients_from_intranet(_key, _ip)}'

            if neighbors:
                for key in neighbors:
                    for sw in neighbors[key]:
                        sw = sw.strip()
                        if with_clients:
                            # print(f'mode: with_clients=True. Prefix "{_key}" ')
                            text += f'{sw}\n{all_neighbor.get_clients_from_intranet(_key, sw)}'
                        else:
                            if row == 0:
                                text += sw + '; \n'
                                row = _default
                            else:
                                text += sw + '; '
                                row -= 1
            if text is None:
                text = "Подключения не найдены. Проверьте правильность параметров."

            _title = f'Все подключения от {_ip} ' + '_' * 20
            QtWidgets.QInputDialog.getMultiLineText(None,
                                                    "Все подключения от свитча",
                                                    _title,
                                                    text=text)

    def work_db(self):
        self.win_db = WorkWithDB(window=self.window_optic)
        self.win_db.show()

    def crea_mv(self):
        self.statusBar().showMessage("Идёт создание вланов ...")
        # Окно запроса начало
        _win = QtWidgets.QDialog()
        _win.setWindowTitle("Создание вланов по списку клиентов из файла.")
        _form = QtWidgets.QFormLayout()

        _city_list = QtWidgets.QComboBox()
        _city_list.addItems(sorted(self.window_optic.city))
        _city_list.setCurrentText(self.window_optic.city_list.currentText())
        _sw_ent = QtWidgets.QLineEdit()
        _sw_ent.setValidator(QtGui.QRegExpValidator(self.window_optic.regexp_ip))
        _port_entry = QtWidgets.QLineEdit()

        file_edit = os.path.abspath(os.getcwd()+settings.client_to_multi_vlan)
        _but_edit = QtWidgets.QPushButton("Редактировать файл с клиентами")
        _but_edit.clicked.connect(lambda: os.startfile(file_edit))
        _but_ok = QtWidgets.QPushButton("Ok")
        _but_ok.clicked.connect(_win.accept)
        _but_cancel = QtWidgets.QPushButton("Cancel")
        _but_cancel.clicked.connect(_win.reject)

        _form.addRow(_city_list)
        _form.addRow("IP свитча: ", _sw_ent)
        _form.addRow("Порт свитча: ", _port_entry)
        _form.addRow(_but_edit)
        _form.addRow(_but_ok, _but_cancel)

        _win.setLayout(_form)
        # Окно запроса конец

        result = _win.exec()
        if result and _sw_ent.text() and _port_entry.text():
            _city = _city_list.currentText()
            state_pref = self.window_optic.city[_city]
            port = _port_entry.text()
            switch = _sw_ent.text()
            clients = []

            path_with_clients = os.path.abspath(os.getcwd() + settings.client_to_multi_vlan)
            try:
                with open(path_with_clients) as f:
                    vlan_list_to_create = f.read().splitlines()
                    vlan_list_to_create = list(filter(None, vlan_list_to_create))
            except Exception as e:
                print(f"Ошибка открытия файла с клиентами: main.py:MainWindow->crea_mv\n{path_with_clients}\n{e}")
            else:
                for client in vlan_list_to_create:
                    client = client.split()
                    vname = client[0]
                    vnum = client[1]
                    tag = 't'
                    _all_data_list = [
                        state_pref,
                        vname,
                        vnum,
                        switch,
                        port,
                        tag,
                    ]
                    clients.append(customers.Customer(*_all_data_list))

                self._thread = CreateMulVlanThread(clients, self.window_optic.p_sw)
                self._thread.mysignal.connect(self.message_out)
                self._thread.start()

    def dele_mv(self):
        self.statusBar().showMessage("Идёт удаление вланов ...")
        # Окно запроса начало
        _win = QtWidgets.QDialog()
        _win.setWindowTitle("Удаление вланов по списку клиентов из файла.")
        _form = QtWidgets.QFormLayout()

        _city_list = QtWidgets.QComboBox()
        _city_list.addItems(sorted(self.window_optic.city))
        _city_list.setCurrentText(self.window_optic.city_list.currentText())
        _sw_ent = QtWidgets.QLineEdit()
        _sw_ent.setValidator(QtGui.QRegExpValidator(self.window_optic.regexp_ip))

        file_edit = os.path.abspath(os.getcwd() + settings.client_to_multi_vlan)
        _but_edit = QtWidgets.QPushButton("Редактировать файл с клиентами")
        _but_edit.clicked.connect(lambda: os.startfile(file_edit))
        _but_ok = QtWidgets.QPushButton("Ok")
        _but_ok.clicked.connect(_win.accept)
        _but_cancel = QtWidgets.QPushButton("Cancel")
        _but_cancel.clicked.connect(_win.reject)

        _form.addRow(_city_list)
        _form.addRow("IP свитча: ", _sw_ent)
        _form.addRow(_but_edit)
        _form.addRow(_but_ok, _but_cancel)

        _win.setLayout(_form)
        # Окно запроса конец

        result = _win.exec()
        if result and _sw_ent.text():
            _city = _city_list.currentText()
            state_pref = self.window_optic.city[_city]
            port = '999'
            switch = _sw_ent.text()
            clients = []

            path_with_clients = os.path.abspath(os.getcwd() + settings.client_to_multi_vlan)
            try:
                with open(path_with_clients) as f:
                    vlan_list_to_create = f.read().splitlines()
                    vlan_list_to_create = list(filter(None, vlan_list_to_create))
            except Exception as e:
                print(f"Ошибка открытия файла с клиентами: main.py:MainWindow->dele_mv\n{path_with_clients}\n{e}")
            else:
                for client in vlan_list_to_create:
                    client = client.split()
                    vname = client[0]
                    vnum = client[1]
                    tag = 't'
                    _all_data_list = [
                        state_pref,
                        vname,
                        vnum,
                        switch,
                        port,
                        tag,
                    ]
                    clients.append(customers.Customer(*_all_data_list))

                self._thread = DelMulVlanThread(clients, self.window_optic.p_sw)
                self._thread.mysignal.connect(self.message_out)
                self._thread.start()


class OpticContentWindow(QtWidgets.QWidget, DecryptPass):
    def __init__(self, parent=None, ico=None):
        super().__init__(parent=parent)
        self.setWindowTitle("Работа с клиентами на оптике.")
        self.parent = parent
        # parent.statusBar().showMessage("Ready")

        if ico:
            self.setWindowIcon(ico)
        self.all_fields_full = 0
        self.city = work_with_db.get_list_cities()  # Словарь горд:ключ
        self.city_pref = {v: k for k, v in self.city.items()}  # Словарь ключ:город

        self.init_ui()

    def init_ui(self):

        # Блок заголовков и полей ввода строками
        label_mnem = QtWidgets.QLabel("Мнемокод: ")
        label_vlan = QtWidgets.QLabel("Номер влана: ")
        label_ipsw = QtWidgets.QLabel("IP свитча: ")
        label_port = QtWidgets.QLabel("Порт: ")

        self.edit_mnem = QtWidgets.QLineEdit()

        self.edit_vlan = QtWidgets.QLineEdit()
        self.edit_vlan.setValidator(QtGui.QIntValidator())

        self.edit_ipsw = QtWidgets.QLineEdit()
        #  валидатор IProotIP
        str_ip = '^((25[0-5]|2[0-4][0-9]|[0-1][0-9]{2}|[0-9]{2}|[0-9])' \
                 '(\.(25[0-5]|2[0-4][0-9]|[0-1][0-9]{2}|[0-9]{2}|[0-9])){3})' \
                 'root' \
                 '((25[0-5]|2[0-4][0-9]|[0-1][0-9]{2}|[0-9]{2}|[0-9])' \
                 '(\.(25[0-5]|2[0-4][0-9]|[0-1][0-9]{2}|[0-9]{2}|[0-9])){3})$;'
        self.regexp_ip = QtCore.QRegExp(str_ip)
        self.edit_ipsw.setValidator(QtGui.QRegExpValidator(self.regexp_ip))

        self.edit_port = QtWidgets.QLineEdit()
        self.edit_port.setValidator(QtGui.QIntValidator())

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
        self.but_free_port = QtWidgets.QPushButton(" Найти свободный порт")
        self.but_free_port.setStatusTip("Найти свободный порт на указанном свитче.")
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

        # self.show()



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
        """ Функция включает/отключает поля и кнопки,
        в зависимости от выбранного действия [удаление, создание, скорость]"""
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
                self.but_free_port.setDisabled(False)
            self.edit_port.setText('')
            self.check_cisco.setText("Создать на Cisco")
            self.edit_port.setDisabled(False)
            self.check_tag.setDisabled(False)

        elif self.rb_delete.isChecked():
            if self.edit_mnem.text() == 'All in file':  # если переходим со вкладки смены скорости
                self.edit_mnem.setText('')
                self.edit_vlan.setText('')
                self.edit_ipsw.setText('')
                self.edit_mnem.setDisabled(False)
                self.edit_vlan.setDisabled(False)
                self.edit_ipsw.setDisabled(False)
                self.check_tag.setDisabled(False)
                self.but_free_port.setDisabled(False)
                self.but_speed_edit.setVisible(False)
                self.check_cisco.setVisible(True)

            self.check_cisco.setText("Удалить с Cisco")
            self.edit_port.setText('999')
            self.edit_port.setDisabled(True)
            self.check_tag.setDisabled(True)

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
            self.but_free_port.setDisabled(True)

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

    def get_free_port(self):
        if self.key_pass:
            print("Свободный порт")
            try:
                _sw = switch.NewSwitch(self.edit_ipsw.text(), sw_passw=self.p_sw)
                res = '\n'.join(_sw.find_free_port())
            except Exception as e:
                print(f"Ошибка при поиске порта {e}")
            else:
                print(f'{res}')
                QtWidgets.QInputDialog.getMultiLineText(None,
                                                        "Свободные порты",
                                                        f"Свободные порты на свитче {self.edit_ipsw.text()}",
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
            mnemo = self.edit_mnem.text().strip()
            vl_number = self.edit_vlan.text()
            switch = self.edit_ipsw.text()
            port = self.edit_port.text()
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
                print("Идёт создание клиента на свитчах")
                self.parent.statusBar().showMessage("Идёт создание клиента на свитчах")
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


class RwrContentWindow(QtWidgets.QWidget, DecryptPass):
    def __init__(self, parent=None, ico=None):
        super().__init__(parent=parent)
        self.setWindowTitle("Работа с клиентами на секторах.")
        self.parent = parent
        # parent.statusBar().showMessage("Ready")

        if ico:
            self.setWindowIcon(ico)
        self.all_fields_full = 0
        self.city = work_with_db.get_list_cities()  # Словарь горд:ключ
        self.city_pref = {v: k for k, v in self.city.items()}  # Словарь префикс:город

        self.init_ui()

    def init_ui(self):

        # Блок заголовков и полей ввода строками
        label_mnem = QtWidgets.QLabel("Мнемокод: ")
        label_vlan = QtWidgets.QLabel("Номер влана: ")
        label_ipsw = QtWidgets.QLabel("IP RWR: ")
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
        self.edit_port.addItems(["eth0", "eth1"])

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
            mnemo = self.edit_mnem.text().strip()
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


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    ico = QtGui.QIcon(settings.ico)
    main_window = MainWindow()
    main_window.setWindowIcon(ico)

    # Запрос ключа для рассшифровки паролей
    dialog_pass = QtWidgets.QInputDialog()
    dialog_pass.setWindowTitle("Ключ для работы с устройствами.")
    dialog_pass.setLabelText("Введите ключ, для разблокировки паролей:")
    dialog_pass.setTextEchoMode(QtWidgets.QLineEdit.Password)
    get_pass = dialog_pass.exec()
    if get_pass == QtWidgets.QDialog.Accepted:
        _key = dialog_pass.textValue()
        DecryptPass.key_pass = _key
        DecryptPass.decrypt_pass()

    main_window.show()

    sys.exit(app.exec_())
