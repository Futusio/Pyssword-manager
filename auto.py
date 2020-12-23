from PyQt5 import QtWidgets, QtCore, QtSql, QtGui
from hashlib import sha256
import smtpd
import psycopg2
import sys
import registration
import recovery
from connect import Connect
from message import Message, Dialog
from main import Scroll
import threading
import os 

conn = QtSql.QSqlDatabase.addDatabase("QSQLITE") # Возможно надо будет перенести в radio
conn.setDatabaseName("main.db")

class ClickableLabel(QtWidgets.QLabel):
    """ Расширения лейбла необходимо для 
    перехвата клика по нему """
    clicked = QtCore.pyqtSignal()
    
    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        self.clicked.emit()

class Authorization(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent, QtCore.Qt.Window)
        self.central = QtWidgets.QWidget()
        self.initUi()
        self.setCentralWidget(self.central)
        self.mode = True # True is Local and reverse 
        # Обработчики
        self.radio_s.toggled.connect(self.change_radio)
        self.button.clicked.connect(self.btn_clicked)
        self.forget_password.clicked.connect(self.go_forget)
        self.registration.clicked.connect(self.go_registration)
        
    def go_forget(self):
        """ Открывает окно восстановления пароля """
        self.forget = recovery.Recovery()
        self.forget.show()

    def go_registration(self):
        """ Открывает окно регистрации """
        self.reg = registration.Registration()
        self.reg.show()

    def initUi(self):
        self.setWindowIcon(QtGui.QIcon("icon.ico"))
        self.setWindowTitle("Вход")
        # Создание виджетов
        question = QtWidgets.QLabel("Где хранить данные?")
        l_login = QtWidgets.QLabel("Логин:")
        l_password = QtWidgets.QLabel("Пароль:")
        self.radio_l = QtWidgets.QRadioButton("Локально")
        self.radio_s = QtWidgets.QRadioButton("Удаленно")
        self.login = QtWidgets.QLineEdit()
        self.password = QtWidgets.QLineEdit()
        self.button = QtWidgets.QPushButton("Войти")
        self.forget_password = ClickableLabel('<a href="/">Восстановить пароль</a>')
        self.registration = ClickableLabel('<a href="/">Регистрация</a>')
        # Настройки виджетов:
        #self.forget_password.setHidden(True)
        #self.registration.setHidden(True)
        self.forget_password.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom)
        self.registration.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignBottom)
        self.password.setEchoMode(QtWidgets.QLineEdit.Password)
        self.radio_l.setChecked(True)
        self.password.setEnabled(False)
        self.radio_l.setToolTip("При выборе этого варианта будет\nиспользоваться локальная база данных.\nДля авторизации достаточно логина пользователя,\nрегистрация не нужна")
        self.radio_s.setToolTip("При выборе этого варианта будет\nиспользоваться удаленная база данных.\nДля авторизации необходим логин и пароль \nранее зарегистрированного пользователя")
        # Grid positions 
        self.grid = QtWidgets.QGridLayout()
        self.grid.addWidget(question,0,0,1,2)
        self.grid.addWidget(self.radio_l,1,0)
        self.grid.addWidget(self.radio_s,1,1)
        self.grid.addWidget(l_login, 2, 0)
        self.grid.addWidget(self.login, 2, 1)
        self.grid.addWidget(l_password, 3,0)
        self.grid.addWidget(self.password,3,1)
        self.grid.addWidget(self.button,4,0,1,2)
        # Layouts
        group = QtWidgets.QGroupBox("Авторизация")
        group.setLayout(self.grid)
        # vbox
        vbox = QtWidgets.QVBoxLayout()
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.forget_password)
        hbox.addWidget(self.registration)
        vbox.addWidget(group)
        vbox.addLayout(hbox)
        self.central.setLayout(vbox)

    def local(self):
        """ В случае подключения к локальной БД"""
        if not os.path.exists("main.db"):
            import createDB # Создаем БД 
        # Поднимаем connect 
        conn.open()
        query = QtSql.QSqlQuery()
        query.exec('SELECT * FROM users WHERE login = \'{}\''.format(
            self.login.text().lower())) # Проверяем в БД наличие соотв. логина 
        if not query.first(): # Если пользователя нет в БД - добавить
            query.prepare("INSERT INTO users VALUES (NULL, ?)")
            query.addBindValue(self.login.text())
            query.exec_()
        # Вытаскиваем id пользователя 
        query.exec('SELECT * FROM users WHERE login = \'{}\''.format(
            self.login.text().lower()))
        query.first()
        uId = query.value('id')
        query.finish()
        conn.close()
        # Открываем главное окно
        self.scroll = Scroll(self.mode, uId, self.login.text(), conn)
        self.scroll.show()
        self.close()

    def remote(self):
        """ Подключение к Удаленной базе данных """
        conn = Connect.connect()
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE login = \'{}\''.format(self.login.text()))
        fetch = cur.fetchall()
        if len(fetch) != 0: # Если не равен нулю - найдены записи таблицы 
            if fetch[0][2] == sha256(bytes(self.password.text(), encoding="UTF-8")).hexdigest():
                suc = Message("Успех", "Авторизация пройдена успешно!", self)
                suc.exec_()
                self.scroll = Scroll(self.mode, fetch[0][0], self.password.text(), conn) # Запускаем главное окно
                self.scroll.show()
                self.close()
            else: 
                msg = Message("Ошибка","Неверный логин или пароль!",self)
                msg.exec_()
        else: # В противном случае нет пользователя
            msg = Message("Ошибка","Пользователя с таким логином не найдено!",self)
            msg.exec_()
        self.key = self.password.text()
        cur.close()

    def btn_clicked(self): # Отрефакторить
        """ Метод авторизации. Проверяет наличия логина в БД
        и сравнивает хеш введенного пароля с хешем в таблице """
        if self.mode: # Локальная БД
            if self.login.text() == "": 
                self.error = Message("Ошибка","Введите Логин!", self)
                self.error.exec_()
                return
            self.local()
            # Если не существует локальной БД - создать
        else: # Удаленная БД
            if self.login.text() == "":
                self.error = Message("Ошибка","Введите Логин!",self)
                self.error.exec_()
                return 
            elif self.password.text() == "":
                self.error = Message("Ошибка","Введите Пароль!",self)
                self.error.exec_()
                return
            self.remote()

    def try_connect(self):
        try:
            self.connect = psycopg2.connect(
                dbname = "main",
                user = "server",
                password = "11111111",
                host = "192.168.56.102",
                port = "5432"
            )
            # В случае успеха изменяем окно
            self.msg.setWindowTitle("Успех")
            self.msg.text.setText("Соединение установлено!")
            self.msg.button.setEnabled(True)
            # # И позволяем вводить данные
            self.password.setDisabled(False)
            self.mode = False
        except psycopg2.OperationalError:
            # В случае неудачи изменяем окно
            self.msg.setWindowTitle("Неудача")
            self.msg.text.setText("Не удалось подключиться к базе данных")
            self.msg.button.setEnabled(True)
            self.radio_l.setChecked(True)



    def change_radio(self):
        """Обработчик переключателя"""
        if self.radio_l.isChecked():
            self.password.setDisabled(True)
            self.mode = True
            #self.forget_password.setHidden(True)
            #self.registration.setHidden(True)
            #self.connect.close()
        # Если выбрана удаленная БД
        elif self.radio_s.isChecked():
            #self.forget_password.setHidden(False)
            #self.registration.setHidden(False)
            self.msg = Message("Подключение", "Установка соединеие с базой данных", self)
            self.msg.button.setEnabled(False)
            thread = threading.Thread(target=self.try_connect)
            thread.start()
            self.msg.exec_()

            

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = Authorization()
    window.show()
    app.exec_()

if __name__=="__main__":
    main()