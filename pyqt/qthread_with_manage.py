from PyQt5 import QtCore, QtWidgets


class MyThread(QtCore.QThread):
    mysignal = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = False
        self.count = 0

    def run(self):
        self.running = True
        while self.running:
            self.count += 1
            self.mysignal.emit(f"Count: {self.count}")
            self.sleep(1)


class MyWindow(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.label = QtWidgets.QLabel("Управление потоком.")
        self.label.setAlignment(QtCore.Qt.AlignHCenter)
        self.start_button = QtWidgets.QPushButton("Запустить поток.")
        self.stop_button = QtWidgets.QPushButton("Остановить поток.")
        self.vbox = QtWidgets.QVBoxLayout()
        self.vbox.addWidget(self.label)
        self.vbox.addWidget(self.start_button)
        self.vbox.addWidget(self.stop_button)
        self.setLayout(self.vbox)

        self.my_thred = MyThread()

        self.start_button.clicked.connect(self.start_thread)
        self.stop_button.clicked.connect(self.stop_thread)
        self.my_thred.mysignal.connect(self.on_change, QtCore.Qt.QueuedConnection)

    def start_thread(self):
        if not self.my_thred.isRunning():
            self.my_thred.start()

    def stop_thread(self):
        self.my_thred.running = False

    def on_change(self, s):
        self.label.setText(s)

    def closeEvent(self, event):
        self.hide()
        self.my_thred.running = False
        self.my_thred.wait(5000)
        event.accept()


if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    window = MyWindow()
    window.setWindowTitle("Приер управления потоками.")
    window.resize(300, 75)

    window.show()

    sys.exit(app.exec())



