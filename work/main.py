from PyQt5 import QtWidgets, QtGui, QtCore
import sys
import os

from work import settings


class MainWindow(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.all_fields_full = 0

        # Блок заголовков и полей ввода строками
        self.label_mnem = QtWidgets.QLabel("Мнемокод: ")
        self.edit_mnem = QtWidgets.QLineEdit()
        # self.edit_mnem.setValidator(QtGui.QIntValidator())

        self.label_vlan = QtWidgets.QLabel("Номер влана: ")
        self.edit_vlan = QtWidgets.QLineEdit()
        self.edit_vlan.setValidator(QtGui.QIntValidator())

        self.label_ipsw = QtWidgets.QLabel("IP свитча: ")
        self.edit_ipsw = QtWidgets.QLineEdit()
        str_ip = '^((25[0-5]|2[0-4][0-9]|[0-1][0-9]{2}|[0-9]{2}|[0-9])' \
                 '(\.(25[0-5]|2[0-4][0-9]|[0-1][0-9]{2}|[0-9]{2}|[0-9])){3})$'
        regexp_ip = QtCore.QRegExp(str_ip)
        self.edit_ipsw.setValidator(QtGui.QRegExpValidator(regexp_ip))

        self.label_port = QtWidgets.QLabel("Порт подклчения: ")
        self.edit_port = QtWidgets.QLineEdit()
        self.edit_port.setValidator(QtGui.QIntValidator())

        self.check_tag = QtWidgets.QCheckBox("Untagged")
        self.check_tag.setToolTip("По умолчанию tagged")

        self.rb_create = QtWidgets.QRadioButton("Создать")
        self.rb_create.setChecked(True)
        self.rb_delete = QtWidgets.QRadioButton("Удалить")
        self.rb_speed = QtWidgets.QRadioButton("Сменить скорость")

        # Блок кнопок и выбора города
        self.city_list = QtWidgets.QComboBox()
        self.city_list.addItems(['Orel', 'Kursk', 'Magnitogorsk', 'Voronezh'])

        # self.city_list.activated.connect(self.city_choise)
        self.but_free_vlan = QtWidgets.QPushButton(" Найти свободный влан")
        self.but_free_port = QtWidgets.QPushButton(" Найти свободный порт")

        # таблица расположения
        self.grid_entry = QtWidgets.QGridLayout()
        self.grid_entry.addWidget(self.label_mnem, 1, 0)
        self.grid_entry.addWidget(self.edit_mnem, 1, 1)
        self.grid_entry.addWidget(self.city_list, 1, 2)

        self.grid_entry.addWidget(self.label_vlan, 2, 0)
        self.grid_entry.addWidget(self.edit_vlan, 2, 1)
        self.grid_entry.addWidget(self.but_free_vlan, 2, 2)

        self.grid_entry.addWidget(self.label_ipsw, 3, 0)
        self.grid_entry.addWidget(self.edit_ipsw, 3, 1)

        self.grid_entry.addWidget(self.label_port, 4, 0)
        self.grid_entry.addWidget(self.edit_port, 4, 1)
        self.grid_entry.addWidget(self.but_free_port, 4, 2)

        self.grid_entry.addWidget(self.check_tag, 5, 1)

        self.grid_entry.addWidget(self.rb_create, 6, 0)
        self.grid_entry.addWidget(self.rb_delete, 6, 1)
        self.grid_entry.addWidget(self.rb_speed, 6, 2)

        self.space_box = QtWidgets.QVBoxLayout()
        self.space_box.setContentsMargins(0, 15, 0, 0)

        self.but_run = QtWidgets.QPushButton("Выполнить")
        self.but_run.setFixedSize(80, 30)
        self.but_run.setDisabled(True)

        # self.btnButton.setDisable(True)
        # self.leInput.textChanged.connect(self.disable_button)
        #
        # def disableButton(self):
        #

        self.vb = QtWidgets.QVBoxLayout()
        self.vb.addLayout(self.grid_entry)
        self.vb.addLayout(self.space_box)
        self.vb.addWidget(self.but_run, alignment=QtCore.Qt.AlignHCenter)

        self.setLayout(self.vb)

        # добавляем события
        self.but_run.clicked.connect(self.run_b)

        self.edit_mnem.textChanged.connect(self.disable_button)
        self.edit_vlan.textChanged.connect(self.disable_button)
        self.edit_ipsw.textChanged.connect(self.disable_button)
        self.edit_port.textChanged.connect(self.disable_button)

        self.rb_create.clicked.connect(self.disable_entry)
        self.rb_delete.clicked.connect(self.disable_entry)
        self.rb_speed.clicked.connect(self.disable_entry)

    def disable_button(self):
        _chek = (len(self.edit_mnem.text())
                 and len(self.edit_vlan.text())
                 and len(self.edit_ipsw.text())
                 and len(self.edit_port.text()))
        if _chek:
            self.but_run.setDisabled(False)
        else:
            self.but_run.setDisabled(True)

    def disable_entry(self):
        if self.rb_create.isChecked():
            if self.edit_mnem.text() == 'All in file':  # если переходим со вкладки смены скорости
                self.edit_mnem.setText('')
                self.edit_vlan.setText('')
                self.edit_ipsw.setText('')
                self.edit_mnem.setDisabled(False)
                self.edit_vlan.setDisabled(False)
                self.edit_ipsw.setDisabled(False)
            self.edit_port.setText('')
            self.edit_port.setDisabled(False)

        elif self.rb_delete.isChecked():
            if self.edit_mnem.text() == 'All in file':  # если переходим со вкладки смены скорости
                self.edit_mnem.setText('')
                self.edit_vlan.setText('')
                self.edit_ipsw.setText('')
                self.edit_mnem.setDisabled(False)
                self.edit_vlan.setDisabled(False)
                self.edit_ipsw.setDisabled(False)
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

            # client_to_change_speed
            try:
                os.startfile(os.path.abspath(os.getcwd() + settings.client_to_change_speed))
            except:
                print("Ошибка открытия файла клиентов со скоростями: {}")

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

    window.show()

    sys.exit(app.exec_())
