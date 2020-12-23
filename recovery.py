from PyQt5 import QtCore, QtWidgets, QtGui
from message import Message
from connect import Connect
from hashlib import sha256
from sender import Sender
import random
import sys
import re

class Recovery(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent, QtCore.Qt.Window)
        self.initUi()
        # Settings 
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.setWindowFlags(
                QtCore.Qt.MSWindowsFixedSizeDialogHint)
        self.setWindowTitle("Восстановление пароля")
        # Events 
        self.code_btn.clicked.connect(self.send_mail)
        self.check_btn.clicked.connect(self.check_code)
        self.ok_btn.clicked.connect(self.end_recovery)

    def initUi(self):
        self.setWindowIcon(QtGui.QIcon("icon.ico"))
        # Create labels
        l_login = QtWidgets.QLabel("Логин:")
        l_mail = QtWidgets.QLabel("Почта:")
        l_code = QtWidgets.QLabel("Почта:")
        l_password = QtWidgets.QLabel("Новый пароль:")
        l_pass_again = QtWidgets.QLabel("Повторите пароль:")
        # textEdits
        self.login = QtWidgets.QLineEdit()
        self.mail = QtWidgets.QLineEdit()
        self.password = QtWidgets.QLineEdit()
        self.pass_again = QtWidgets.QLineEdit()
        self.enter_code = QtWidgets.QLineEdit()
        # Buttons 
        self.code_btn = QtWidgets.QPushButton("Получить код")
        self.check_btn = QtWidgets.QPushButton("Проверить код")
        self.ok_btn = QtWidgets.QPushButton("Сменить пароль")
        # Grid 
        grid = QtWidgets.QGridLayout()
        grid.addWidget(l_login, 0, 0)
        grid.addWidget(self.login, 0, 1)
        grid.addWidget(l_mail, 1, 0)
        grid.addWidget(self.mail, 1, 1)
        grid.addWidget(l_code, 2, 0)
        grid.addWidget(self.code_btn, 2, 1)
        grid.addWidget(self.enter_code, 3, 0)
        grid.addWidget(self.check_btn, 3, 1)
        grid.addWidget(l_password, 4, 0)
        grid.addWidget(self.password, 4, 1)
        grid.addWidget(l_pass_again, 5, 0)
        grid.addWidget(self.pass_again, 5, 1)
        # Settings 
        self.enter_code.setEnabled(False)
        self.password.setEnabled(False)
        self.pass_again.setEnabled(False)
        self.password.setEchoMode(QtWidgets.QLineEdit.Password)
        self.pass_again.setEchoMode(QtWidgets.QLineEdit.Password)
        # Layouts 
        group = QtWidgets.QGroupBox("Восстановление пароля")
        group.setLayout(grid)
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(group)
        vbox.addWidget(self.ok_btn)
        self.setLayout(vbox)
    
    def send_mail(self):
        """ Отправляем письмо с кодом восстановления """
        if self.login.text() == "" and self.mail.text() == "":
            # Проверка пустоты строк 
            Message("Ошибка", "Поля \'логин\' и \'почта\' должны быть заполненны", self).exec_()
        pattern=r'(^|\s)[-a-z0-9_.]+@([-a-z0-9]+\.)+[a-z]{2,6}(\s|$)' # Регулярка почты
        re_pat=re.compile(pattern)
        is_valid = re_pat.match(self.mail.text().lower())
        if is_valid: # Проверка валидности адреса
            conn = Connect.connect()
            cur = conn.cursor()
            cur.execute('SELECT * FROM users WHERE login = \'{}\' and email = \'{}\''.format(
                self.login.text().lower() , self.mail.text().lower()
            ))
            if len(cur.fetchall()) != 0: # Проверка наличия логина и почты в БД 
                # Отправка письма 
                self.code = ''.join([str(random.randint(0,9)) for _ in range(6)])
                sender = Sender()
                sender.send_rec(self.mail.text(), self.code)
                # Меняем виджеты
                self.login.setEnabled(False)
                self.mail.setEnabled(False)
                self.enter_code.setEnabled(True)
            else: 
                Message("Ошибка",'Указаный аккаунт не найден',self).exec_()
            cur.close()
            conn.close()
        else: # В случае невалидности введенной почты
            Message("Ошибка","Введен неверный формат почты", self).exec_()

    def check_code(self):
        """ Проверка корректности ввода кода восстановления """
        if self.enter_code.text() == self.code:
            Message("Успех","Код восстановления верный!", self).exec_()
            self.password.setEnabled(True)
            self.pass_again.setEnabled(True)
            self.enter_code.setEnabled(False)
        else: 
            Message("Ошибка","Неверный код восстановления", self).exec_()

    def end_recovery(self):
        """ Изменения поля пароль в БД """
        if self.password.text() == self.pass_again.text(): # Проверка валидности пароля
            conn = Connect.connect()
            cur = conn.cursor()
            cur.execute('UPDATE users SET password = \'{}\' WHERE login = \'{}\' and email = \'{}\''.format(
                sha256(bytes(self.password.text(), encoding="UTF-8")).hexdigest(),
                self.login.text(),
                self.mail.text()
            ))
            conn.commit()
            cur.close()
            conn.close()
            Message("Успех","Пароль пользователя успешно изменен!", self).exec_()
            self.close()
        else: # Если пароли не совпадают
            Message("Ошибка","Пароли должны совпадать!", self).exec_()