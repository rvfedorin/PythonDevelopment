from PyQt5 import QtWidgets, QtGui
import sys


class MainWindow(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    ico = QtGui.QIcon("ico.jpg")
    window = MainWindow()
    window.setWindowTitle("Работа с клиентами.")
    window.resize(400, 150)
    window.setWindowIcon(ico)

    window.show()

    sys.exit(app.exec_())
