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
            