from PyQt5 import QtWidgets


class MyLineEdit(QtWidgets.QLineEdit):
    def __init__(self, _id, parent=None):
        super().__init__(parent)
        self.id = _id

    def focusInEvent(self, e):
        print(f"Получен фокус полем {self.id}")
        QtWidgets.QLineEdit.focusInEvent(self, e)

    def focusOutEvent(self, e):
        print(f"Потерян фокус {self.id}")
        QtWidgets.QLineEdit.focusOutEvent(self, e)


class MyWindow(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Управлене фокусом.")
        self.resize(300, 80)
        self.ent1 = MyLineEdit(1)
        self.ent2 = MyLineEdit(2)
        self.button = QtWidgets.QPushButton("Установить фокус на кнопку 2")
        self.vbox = QtWidgets.QVBoxLayout()
        self.vbox.addWidget(self.button)
        self.vbox.addWidget(self.ent1)
        self.vbox.addWidget(self.ent2)
        self.setLayout(self.vbox)

        self.button.clicked.connect(self.on_cl)
        # Задаём порядок объода с помощью TAB
        QtWidgets.QWidget.setTabOrder(self.ent1, self.ent2)
        QtWidgets.QWidget.setTabOrder(self.ent2, self.button)

    def on_cl(self):
        self.ent2.setFocus()


if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    win = MyWindow()

    win.show()

    sys.exit(app.exec_())
