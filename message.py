from PyQt5 import QtWidgets, QtCore

class Message(QtWidgets.QDialog):
    """ Данное окно будет отображаться 
    в случае неккоретктного ввода имени
    группы с информацией о ошибке""" 
    def __init__(self, title, message, parent=None):
        super().__init__(parent)
        # Настройки окна
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.setWindowFlags(
                QtCore.Qt.Window |
                QtCore.Qt.WindowTitleHint |
                QtCore.Qt.MSWindowsFixedSizeDialogHint)
        self.setWindowTitle(title)
        # Создания виджета
        self.vBox = QtWidgets.QVBoxLayout()
        self.text = QtWidgets.QLabel(message)
        self.button = QtWidgets.QPushButton("ок")
        self.button.clicked.connect(self.close)
        # Установки 
        self.vBox.addWidget(self.text)
        self.vBox.addWidget(self.button)
        self.setLayout(self.vBox)

class Dialog(QtWidgets.QDialog):
    def __init__(self, title, text, parent = None):
        super().__init__(parent)
        self.text = text
        self.setWindowTitle(title)
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.setWindowFlags(
                QtCore.Qt.Window |
                QtCore.Qt.WindowTitleHint |
                QtCore.Qt.MSWindowsFixedSizeDialogHint)
        self.initUi()

    def initUi(self):
        # Widgets 
        text = QtWidgets.QLabel(self.text)
        text.setAlignment(QtCore.Qt.AlignCenter)
        self.accept = QtWidgets.QPushButton("Да")
        self.reject = QtWidgets.QPushButton("Нет")
        # Layouts 
        widget = QtWidgets.QWidget()
        vBox = QtWidgets.QVBoxLayout()
        hBox = QtWidgets.QHBoxLayout()
        hBox.addWidget(self.reject)
        hBox.addWidget(self.accept)
        widget.setLayout(hBox)
        vBox.addWidget(text)
        vBox.addWidget(widget)
        self.setLayout(vBox)
        # Settings 