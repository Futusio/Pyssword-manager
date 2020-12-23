from PyQt5 import QtWidgets, QtCore, QtGui
from hashlib import sha256
from sender import Sender
import psycopg2
from psycopg2 import sql
import sys
import random
import re
from message import Message
from connect import Connect
from hashlib import sha256


class Registration(QtWidgets.QWidget):
    def __init__(self, parent=None):
        # initUi
        super().__init__(parent, QtCore.Qt.Window)
        self.initUi()
        # flags 
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.setWindowFlags(
                QtCore.Qt.MSWindowsFixedSizeDialogHint)
        self.setWindowTitle("Регистрация")
        # events 
        self.get_btn.clicked.connect(self.send_mail)
        self.code_btn.clicked.connect(self.check_code)
        self.ok_btn.clicked.connect(self.end_registration)

    def initUi(self):
        self.setWindowIcon(QtGui.QIcon("icon.ico"))
        # Labels 
        l_login = QtWidgets.QLabel("Логин:")
        l_mail = QtWidgets.QLabel("Почта:")
        l_pass = QtWidgets.QLabel("Пароль:")
        l_again = QtWidgets.QLabel("Повтор:")
        l_code = QtWidgets.QLabel("Код:")
        # TextEdits
        self.login = QtWidgets.QLineEdit()
        self.mail = QtWidgets.QLineEdit()
        self.password = QtWidgets.QLineEdit()
        self.password_again = QtWidgets.QLineEdit()
        self.code_line = QtWidgets.QLineEdit()
        self.login.setPlaceholderText("login")
        self.mail.setPlaceholderText("mail@example.com")
        self.password.setPlaceholderText("11111111")
        self.password_again.setPlaceholderText("11111111")
        self.password.setEchoMode(QtWidgets.QLineEdit.Password)
        self.password_again.setEchoMode(QtWidgets.QLineEdit.Password)
        self.code_line.setEnabled(False)    
        # buttons
        self.get_btn = QtWidgets.QPushButton("Получить код")
        self.code_btn = QtWidgets.QPushButton("Проверить код")
        self.ok_btn = QtWidgets.QPushButton("Регистрация")
        self.code_btn.setEnabled(False)
        self.ok_btn.setEnabled(False)
        # GridLayer
        grid = QtWidgets.QGridLayout()
        grid.addWidget(l_login, 0, 0)
        grid.addWidget(l_mail, 1, 0)
        grid.addWidget(l_pass, 2, 0)
        grid.addWidget(l_again, 3, 0)
        grid.addWidget(self.login, 0, 1)
        grid.addWidget(self.mail, 1, 1)
        grid.addWidget(self.password, 2, 1)
        grid.addWidget(self.password_again, 3, 1)
        grid.addWidget(l_code, 4, 0)
        grid.addWidget(self.get_btn, 4, 1)
        grid.addWidget(self.code_line, 5, 0)
        grid.addWidget(self.code_btn, 5, 1)
        # Set Layouts 
        vbox = QtWidgets.QVBoxLayout()
        group = QtWidgets.QGroupBox("Регистрация")
        group.setLayout(grid)        
        vbox.addWidget(group)
        vbox.addWidget(self.ok_btn)
        self.setLayout(vbox)
    
    def end_registration(self):
        """ Метод записывает в таблицу
        нового пользователя """
        conn = Connect.connect() # Поднимаем коннект
        cur = conn.cursor()
        query = sql.SQL('INSERT INTO users (login, password, email) VALUES (\'{}\', \'{}\', \'{}\')'.format(
            self.login.text().lower(), 
            sha256(bytes(self.password.text(), encoding="UTF-8")).hexdigest(), # Хешуем хешуем хешуем стиль хешуем
            self.mail.text().lower()
        ))
        cur.execute(query)
        conn.commit()
        cur.close()
        conn.close()
        Message("Успех","Регистрация успешно заверешна!", self).exec_()
        self.close()

    def check_code(self):
        """Метод проверяет верность кода"""
        if self.code_line.text() == self.code: # Если код подходит
            Message("Успех", "Введен корректный код", self).exec_()
            self.login.setEnabled(False)
            self.mail.setEnabled(False)
            self.password.setEnabled(False)
            self.password_again.setEnabled(False)
            self.code_line.setEnabled(False)
            self.get_btn.setEnabled(False)
            self.ok_btn.setEnabled(True)
        else: 
            Message("Ошибка","Введен неверный код!", self).exec_()

    def check_send(self):
        """Проверка валидности формы регистрации"""
        if self.login.text() == "": # Логин
            return "Поле \"логин\" должно быть заполненно"
        elif self.mail.text() == "": # Почта 
            return "Поле \"почта\" должно быть заполненно"
        elif self.password.text() == "": # Пароль
            return "Поле \"пароль\" должно быть заполненно"
        elif self.password_again.text() == "": # Пароль еще 
            return "Поле \"пароль еще раз\" должно быть заполненно"
        elif self.password_again.text() != self.password.text(): # Пароли должны совпадать
            return "Поля \"пароль\" и \"повтор пароля\" должны совпадать"
        pattern=r'(^|\s)[-a-z0-9_.]+@([-a-z0-9]+\.)+[a-z]{2,6}(\s|$)' # Регулярка почты
        re_pat=re.compile(pattern)
        is_valid = re_pat.match(self.mail.text().lower())
        if not is_valid: # Регулярка почты
            return "Поле адреса должно быть в формате \n\texample@server.com"
        # Ниже проверка уникальности ввода логина и почты
        conn = Connect.connect()
        cur = conn.cursor()
        cur.execute('SELECT * FROM users')
        for row in cur.fetchall():
            if self.login.text().lower() in row: # Проверка логина
                cur.close()
                conn.close()
                return "Пользователь с таким логином уже зарегистрирован"
            elif self.mail.text().lower() in row: # Проверка почты
                cur.close()
                conn.close()
                return "Пользователь с такой почтой уже зарегистрирован"
        # Если дошли до сюду вернем True
        return True

    def send_mail(self):
        """В случае валидности ввода метод
        отправляет сообщение с кодом регистрации """
        if self.check_send() == True: # True
            self.code = ''.join([str(random.randint(0,9)) for _ in range(6)])
            # Email
            sender = Sender()
            sender.send_reg(self.mail.text(), self.code)
            # do
            self.code_btn.setEnabled(True)
            self.code_line.setEnabled(True)
        else: # Сообщение об ошибке
            Message("Ошибка", "{}".format(self.check_send()), self).exec_()