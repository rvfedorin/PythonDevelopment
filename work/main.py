from PyQt5 import QtWidgets
import sys


class MainWindow(QtWidgets.QWidget):
    def __init__(self, parent):
        super().__init__(parent)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.setWindowTitle("Работа с клиентами.")
    window.resize(400, 150)

    window.show()

    sys.exit(app.exec_())
