from PyQt5 import QtCore, QtGui, QtWidgets
import sys

app = QtWidgets.QApplication(sys.argv)
window = QtWidgets.QWidget()
window.setWindowFlags( QtCore.Qt.FramelessWindowHint)
window.setWindowTitle ("App window ")
window.resize(479, 198)
pixmap = QtGui.QPixmap("45.jpg")
pal = window.palette()
pal.setBrush(QtGui.QPalette.Normal, QtGui.QPalette.Window,QtGui.QBrush(pixmap))
pal.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Window,QtGui.QBrush(pixmap))
window.setPalette(pal)
window.setMask(pixmap.mask())
button = QtWidgets.QPushButton("quit", window)
button.setFixedSize(50, 30)
button.move(75, 135)
button.clicked.connect(QtWidgets.qApp.quit)
window.show()
sys.exit(app.exec_())