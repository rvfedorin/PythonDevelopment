from PyQt5 import QtWidgets, QtCore, QtGui
import time


class MyWindow(QtWidgets.QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setText("Закрыть окно")
        self.clicked.connect(QtWidgets.qApp.quit)

    def load_data(self, sp):
        for i in range(1, 10):
            time.sleep(1)
            sp.showMessage(f"Загрузка данных... {i*10}%",
                           QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom,
                           QtCore.Qt.black)
            QtWidgets.qApp.processEvents()


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)

    splash = QtWidgets.QSplashScreen(QtGui.QPixmap("img.jpg"))
    splash.showMessage("Загрузка данных... 0%",
                               QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom,
                               QtCore.Qt.black)
    splash.show()
    QtWidgets.qApp.processEvents()

    window = MyWindow()
    window.setWindowTitle("Использование классв QSplashScreen")
    window.resize(300, 80)
    window.load_data(splash)
    window.show()

    splash.finish(window)

    sys.exit(app.exec_())


