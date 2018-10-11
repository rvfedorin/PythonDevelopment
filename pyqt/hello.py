from PyQt5 import QtWidgets
import sys

app = QtWidgets.QApplication(sys.argv)  # Создаём приложение, всегда одно
window = QtWidgets.QWidget()  # создаём окно, по сути root
window.setWindowTitle("Hello, world!")
window.resize(300, 70)  # минимальные размеры окна ширинаХвысота

label = QtWidgets.QLabel("<center>Пирвет, мир!!!</center>")
btnQuit = QtWidgets.QPushButton("&Закрыть окно.")  # & - задаёт быстрый доступ по Alt+З
vbox = QtWidgets.QVBoxLayout()  # вертикальный контейнер, вседобавления сверху вниз
vbox.addWidget(label)
vbox.addWidget(btnQuit)

window.setLayout(vbox)

btnQuit.clicked.connect(app.quit)
window.show()
sys.exit(app.exec_())
