from PyQt5 import QtWidgets, QtGui
import sys


class MainWindow(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Блок заголовков и полей ввода строками
        self.label_mnem = QtWidgets.QLabel("Мнемокод: ")
        self.edit_mnem = QtWidgets.QLineEdit()

        self.label_vlan = QtWidgets.QLabel("Номер влана: ")
        self.edit_vlan = QtWidgets.QLineEdit()

        self.label_ipsw = QtWidgets.QLabel("IP свитча: ")
        self.edit_ipsw = QtWidgets.QLineEdit()

        self.label_port = QtWidgets.QLabel("Порт подклчения: ")
        self.edit_port = QtWidgets.QLineEdit()

        self.check_tag = QtWidgets.QCheckBox("Untagged")

        self.rb_create = QtWidgets.QRadioButton("Создать")
        self.rb_create.setChecked(True)
        self.rb_delete = QtWidgets.QRadioButton("Удалить")
        self.rb_speed = QtWidgets.QRadioButton("Сменить скорость")

        # Блок кнопок и выбора города
        self.city_list = QtWidgets.QComboBox()
        self.city_list.addItems(['Orel', 'Kursk', 'Magnitogorsk', 'Воронеж'])
        self.city_list.activated.connect(self.city_choise)
        self.but_free_vlan = QtWidgets.QPushButton("Найти свободный влан")
        self.but_free_port = QtWidgets.QPushButton("Найти свободный порт")
        self.but_run = QtWidgets.QPushButton("Выполнить")

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

        self.vb = QtWidgets.QVBoxLayout()
        self.vb.addLayout(self.grid_entry)
        self.vb.addLayout(self.space_box)
        self.vb.addWidget(self.but_run)

        self.setLayout(self.vb)

    def city_choise(self):
        pass





if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    ico = QtGui.QIcon("ico.jpg")
    window = MainWindow()
    window.setWindowTitle("Работа с клиентами.")
    window.resize(400, 200)
    window.setWindowIcon(ico)

    window.show()

    sys.exit(app.exec_())
