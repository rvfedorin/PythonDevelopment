from PyQt5 import QtCore, QtWidgets


class MyWindow(QtWidgets.QWidget):
    mysignal = QtCore.pyqtSignal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Генерация сигнала из программы")
        self.resize(300, 80)
        self.button1 = QtWidgets.QPushButton("Нажми меня")
        self.button2 = QtWidgets.QPushButton("Кнопка 2")
        self.vbox = QtWidgets.QVBoxLayout()
        self.vbox.addWidget(self.button1)
        self.vbox.addWidget(self.button2)
        self.setLayout(self.vbox)
        self.button1.clicked.connect(self.on_but1)
        self.button2.clicked.connect(self.on_but2)
        self.mysignal.connect(self.on_sig)

    def on_but1(self):
        print("Нажата кнопка 1")
        # Генерируем сигнал
        self.button2.clicked[bool].emit(True)
        self.mysignal.emit(10, 20)

    def on_but2(self):
        print("Нажата кнопка 2")

    def on_sig(self, x, y):
        print("Обработан пользовательский сигнал on_sig()")
        print(f"x={x}, y={y}")


if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    window = MyWindow()
    window.show()

    sys.exit(app.exec_())

