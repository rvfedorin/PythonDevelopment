from PyQt5 import QtWidgets, QtCore
import sys


class MyWindow(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(MyWindow, self).__init__(parent)
        self.label = QtWidgets.QLabel("Привет, мир!")
        self.label.setAlignment(QtCore.Qt.AlignHCenter)
        self.btnQuit = QtWidgets.QPushButton("Закрыть.")
        self.vbox = QtWidgets.QVBoxLayout()
        self.vbox.addWidget(self.label)
        self.vbox.addWidget(self.btnQuit)
        self.setLayout(self.vbox)

        self.btnQuit.clicked.connect(QtWidgets.qApp.quit)


class MyDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(MyDialog, self).__init__(parent)
        self.myWidget = MyWindow()
        self.myWidget.vbox.setContentsMargins(0, 0, 0, 0)
        self.button = QtWidgets.QPushButton("&Изменить надпись.")
        main_box = QtWidgets.QVBoxLayout()
        main_box.addWidget(self.myWidget)
        main_box.addWidget(self.button)
        self.setLayout(main_box)
        self.button.clicked.connect(self.on_clicked)

    def on_clicked(self):
        self.myWidget.label.setText("Новый текст!!")
        self.button.setDisabled(True)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MyDialog()
    window.resize(300, 70)
    window.show()

    sys.exit(app.exec_())
