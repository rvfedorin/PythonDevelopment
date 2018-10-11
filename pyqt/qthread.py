from PyQt5 import QtCore, QtWidgets


class MyThread(QtCore.QThread):
    mysignal = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super(MyThread, self).__init__(parent)

    def run(self):
        for i in range(1, 21):
            self.sleep(3)
            self.mysignal.emit(f"i = {i}")


class MyWindow(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(MyWindow, self).__init__(parent)
        self.label = QtWidgets.QLabel("Нажмите кнопкку для запуска потока.")
        self.label.setAlignment(QtCore.Qt.AlignHCenter)
        self.button = QtWidgets.QPushButton("Запустить процесс.")

        self.vbox = QtWidgets.QVBoxLayout()
        self.vbox.addWidget(self.label)
        self.vbox.addWidget(self.button)
        self.setLayout(self.vbox)
        self.my_thread = MyThread()

        self.button.clicked.connect(self.on_clicked)
        self.my_thread.started.connect(self.on_started)
        self.my_thread.finished.connect(self.on_finished)
        self.my_thread.mysignal.connect(self.on_changed, QtCore.Qt.QueuedConnection)

    def on_clicked(self):
        self.button.setDisabled(True)
        self.my_thread.start()

    def on_started(self):
        self.label.setText("Вызван метод on_started()")

    def on_finished(self):
        self.label.setText("Вызван метод on_finished()")
        self.button.setDisabled(False)

    def on_changed(self, s):
        self.label.setText(s)


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    window = MyWindow()
    window.setWindowTitle("Пример работы с потоками.")
    window.resize(300, 75)
    window.show()

    sys.exit(app.exec())
