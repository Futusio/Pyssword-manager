from PyQt5 import QtWidgets, QtCore, QtSql, QtGui
import pyperclip
from message import Message, Dialog
from psycopg2 import sql
from random import randint
from cipher import Cipher


class NewAccount(QtWidgets.QWidget):
    """ Окно в которое будут вводиться 
    все данные необходимые для занесения
    аккаунта в базу данных"""
    def __init__(self, tree, mode, u_id, g_id, connect, key, old = False, parent=None, brother=None):
        super().__init__(parent, QtCore.Qt.Window)
        # Настройки окна
        self.key = key
        self.connect = connect # Есть контакт 
        self.brother = brother # Уже забыл 
        self.old = old # False - Создать новый аккаунт. True - изменить старый
        self.mode = mode
        self.g_id = g_id 
        self.u_id = u_id
        self.tree = tree
        self.parent_name = tree.currentItem().parent().text(0)
        self.set_sId() # Вытаскиваем s_ID 
        self.initUI() # Заполняем Виджет 
        # Обработчики
        self.ok_btn.clicked.connect(self.ok_clicked)
        self.rnd.clicked.connect(self.rnd_clicked)

    def set_sId(self):
        """ Вытаскиваем s_id из Баз данных """
        if self.mode: # Локальной БД 
            self.connect.open()
            query = QtSql.QSqlQuery()
            query.exec("SELECT id FROM sites WHERE name = \"{}\" AND g_id = {}".format(self.parent_name, self.g_id))
            query.first()
            self.s_id = query.value("id")
            query.finish()
            self.connect.close()
        else: # Удаленной БД
            cursor = self.connect.cursor()
            cursor.execute("SELECT * FROM sites WHERE name=\'{}\' AND g_id=\'{}\'".format(self.parent_name, self.g_id))
            self.s_id = cursor.fetchone()[0]
            cursor.close()

    def initUI(self):
        """Отображение окна"""
        self.setWindowIcon(QtGui.QIcon("icon.ico"))
        self.setWindowTitle("Добавить аккаунт " + self.parent_name)
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        # Создание виджетов 
        label_1 = QtWidgets.QLabel("Введите название:")
        label_2 = QtWidgets.QLabel("Введите логин:")
        label_3 = QtWidgets.QLabel("Введите пароль:")
        label_4 = QtWidgets.QLabel("Дополнительная\nинформация: ")
        if self.old: # На случай, изменениня аккаунта
            self.textbox_1 = QtWidgets.QLineEdit(self.brother.textbox_1.text())
            self.textbox_2 = QtWidgets.QLineEdit(self.brother.textbox_2.text())
            try:
                self.rich_box = QtWidgets.QTextEdit(self.brother.rich_box.toPlainText())
            except AttributeError: 
                self.rich_box = QtWidgets.QTextEdit()
            self.ok_btn = QtWidgets.QPushButton("Изменить")
        else:  # Создание нового аккаунта 
            self.textbox_1 = QtWidgets.QLineEdit()
            self.textbox_2 = QtWidgets.QLineEdit()
            self.rich_box = QtWidgets.QTextEdit()
            self.ok_btn = QtWidgets.QPushButton("Добавить")
        self.textbox_3 = QtWidgets.QLineEdit()
        self.textbox_3.setEchoMode(QtWidgets.QLineEdit.Password)
        self.rnd = QtWidgets.QPushButton("Случайный пароль")
        # Наполнение компоновщика 
        grid = QtWidgets.QGridLayout()
        grid.addWidget(label_1, 0,0) # Сначала накинул лейблы
        grid.addWidget(label_2, 1,0)
        grid.addWidget(label_3, 2,0)
        grid.addWidget(label_4, 3,0)
        grid.addWidget(self.textbox_1, 0, 1, 1, 2) # Накидываем текстовые поля
        grid.addWidget(self.textbox_2, 1, 1, 1, 2)
        grid.addWidget(self.textbox_3, 2, 1, 1, 1) 
        grid.addWidget(self.rich_box, 3, 1, 1, 2)
        grid.addWidget(self.rnd, 2, 2, 1, 1) # И кнопкиshow 
        grid.addWidget(self.ok_btn, 4, 2, 1,1)
        self.setLayout(grid)

    def ok_clicked(self):
        # Шифруем важные данные и пакуем в json 
        login = Cipher.encrypt(self.textbox_2.text(), self.key)
        password = Cipher.encrypt(self.textbox_3.text(), self.key)
        # Добавление в базу данных
        if self.mode:
            self.connect.open()
            query = QtSql.QSqlQuery()
            query.prepare("INSERT INTO accounts VALUES (NULL, ?, ?, ?, ?, ?, ?, ?)")
            query.addBindValue(self.u_id)
            query.addBindValue(self.g_id)
            query.addBindValue(self.s_id)
            query.addBindValue(self.textbox_1.text())
            query.addBindValue(login)
            query.addBindValue(password)
            query.addBindValue(self.rich_box.toPlainText())
            if not query.exec_(): # Проверка успешности запроса 
                error = Message("Ошибка","Неизвестная ошибка!\nПерезагрузите приложение", self)
                error.exec_()
                query.finish()
                self.connect.close()
                self.close()
                return
            query.finish()
            self.connect.close()
        else: 
            cursor = self.connect.cursor()
            query = sql.SQL("""
                INSERT INTO accounts (u_id, g_id, s_id, name, login, password, about) 
                VALUES (\'{}\',\'{}\',\'{}\',\'{}\',\'{}\',\'{}\',\'{}\')""".format(
                    self.u_id, self.g_id, self.s_id, self.textbox_1.text(), login,
                    password, self.rich_box.toPlainText()
                ))
            if cursor.execute(query) is None:
                self.connect.commit()
            else:
                Message("Ошибка","Неизвестная ошибка!\nПерезагрузите приложение", self).exec_()
                self.close()
                return 
            cursor.close()
        # Удаление и добавление статичной ветви 
        self.tree.currentItem().parent().addChild(QtWidgets.QTreeWidgetItem([self.textbox_1.text()]))
        self.tree.currentItem().parent().removeChild(
            self.tree.currentItem().parent().child(
                self.tree.currentItem().parent().childCount() - 2))
        self.tree.currentItem().parent().addChild(QtWidgets.QTreeWidgetItem(["Добавить"]))
        if self.old: # На случай изменения аккаунта 
            successful = Message("Успех", "Аккаунт успешно изменен!", self)
            successful.exec_()
        else:  # На случай добавления аккаунта 
            successful = Message("Успех", "Аккаунт успешно добавлен!", self)
            successful.exec_()
        # Создания виджета 
        self.close()

    def rnd_clicked(self, symbols = True): # Написать модуль рандомного создания пароля 
        """ if symbols == True
        we use also _,*,!,&,? and another"""
        other = ['*','!','?','-','_','.','&']*5 # Массив символов
        upper = [chr(i) for i in range(65,91)] # Массив больших букв
        lower = [chr(i) for i in range(97,123)] # Массив маленьких букв
        numbers = [str(i) for i in range(0,10)] # Массив чисел
        array = upper + lower + numbers + other # Массив всех возможных элементов
        # Генерируем пароль и возвращаем его строкой
        password = [array[randint(0,len(array)-1)] for _ in range(randint(8,24))]
        self.textbox_3.setText( ''.join(password))


class Account(QtWidgets.QWidget):
    """ Окно отображения информации об аккаунте """
    def __init__(self, tree, mode, u_id, g_id, connect, key, parent = None):
        super().__init__(parent, QtCore.Qt.Window)
        # Settings
        self.key = key
        self.rich = False
        self.connect = connect
        self.tree = tree
        self.mode = mode
        self.name = tree.currentItem().text(0)
        self.u_id = u_id
        self.g_id = g_id
        # Fill Widgets 
        if mode: self.local()
        else: self.remote()
        self.initUI()
        # Events
        self.change_btn.clicked.connect(self.click_change)
        self.delete_btn.clicked.connect(self.click_delete)
        self.copy_login.clicked.connect(self.c_login)
        self.copy_passw.clicked.connect(self.c_passw)
        # Настройки окна 

    def c_login(self):
        """ Копирование логина и отображение сообщения"""
        pyperclip.copy(self.textbox_2.text())
        Message("Успех", "Логин скопирован в буфер обмена", self).exec_()

    def c_passw(self):
        pyperclip.copy(self.textbox_3.text())
        Message("Успех", "Пароль скопирован в буфер обмена", self).exec_()

    def initUI(self):
        """Интерфейс виджетов"""
        self.setWindowIcon(QtGui.QIcon("icon.ico"))
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.setWindowTitle("Информация об аккаунте")
        # Четыре лейбла 
        self.label_1 = QtWidgets.QLabel("Название:") #
        self.label_2 = QtWidgets.QLabel("Логин:")
        self.label_3 = QtWidgets.QLabel("Пароль:")
        self.label_4 = QtWidgets.QLabel("Дополнительная информация:")
        # Кнопочки сохраненния данных в буфер 
        self.copy_login = QtWidgets.QPushButton("Скопировать")
        self.copy_passw  = QtWidgets.QPushButton("Скопировать")
        # Четыре поля ввода
        self.textbox_1.setDisabled(True)
        self.textbox_2.setDisabled(True)
        self.textbox_3.setDisabled(True)
        self.textbox_3.setEchoMode(QtWidgets.QLineEdit.Password)
        self.change_btn = QtWidgets.QPushButton("Изменить")
        self.delete_btn = QtWidgets.QPushButton("Удалить")
        # Размещение по сетке grid 
        grid = QtWidgets.QGridLayout()
        grid.addWidget(self.label_1, 0, 0, 1, 2)
        grid.addWidget(self.textbox_1, 0, 2, 1, 2)
        grid.addWidget(self.label_2, 1, 0, 1, 2)
        grid.addWidget(self.textbox_2, 1, 2, 1, 1)
        grid.addWidget(self.copy_login, 1, 3, 1, 1)
        grid.addWidget(self.label_3, 2, 0, 1, 2)
        grid.addWidget(self.textbox_3, 2, 2, 1, 1)
        grid.addWidget(self.copy_passw, 2, 3, 1, 1)
        if self.rich: # В зависимости от заполненности RichBox
            self.rich_box.setDisabled(True)
            grid.addWidget(self.label_4, 3, 0, 1, 2)
            grid.addWidget(self.rich_box, 3, 2, 1, 2)
        grid.addWidget(self.delete_btn, 4, 0, 1, 2)
        grid.addWidget(self.change_btn, 4, 2, 1, 2)
        # Связь окна с виджетами
        self.setLayout(grid)

# Методы заполнения окна отображения аккаунта 
    def local(self):
        self.connect.open()
        query = QtSql.QSqlQuery()
        query.exec(
            "SELECT * FROM accounts WHERE name = \"{}\" and u_id =\"{}\" and g_id=\"{}\"".format(
                self.name, self.u_id, self.g_id))
        query.first()
        if query.value("about") != "": self.rich = True # Если about не пуст - будем отображать RichBox
        self.textbox_1 = QtWidgets.QLineEdit(query.value("name"))
        self.textbox_2 = QtWidgets.QLineEdit(Cipher.decrypt(query.value("login"), self.key).decode('utf-8'))
        self.textbox_3 = QtWidgets.QLineEdit(Cipher.decrypt(query.value("passw"), self.key).decode('utf-8'))
        if self.rich:
            self.rich_box = QtWidgets.QTextEdit(query.value("about"))
        query.finish()
        self.connect.close()
    
    def remote(self):
        cursor = self.connect.cursor()
        query = sql.SQL("SELECT * FROM accounts WHERE name=\'{}\' AND u_id=\'{}\' and g_id=\'{}\'".format(
            self.name, self.u_id, self.g_id
        ))
        cursor.execute(query)
        fetch = cursor.fetchone()
        login = Cipher.decrypt(fetch[5], self.key)
        password = Cipher.decrypt(fetch[6], self.key)
        if fetch[7] != "": self.rich = True # Аналогично local --> if
        self.textbox_1 = QtWidgets.QLineEdit(fetch[4])
        self.textbox_2 = QtWidgets.QLineEdit(login.decode('utf-8'))
        self.textbox_3 = QtWidgets.QLineEdit(password.decode('utf-8'))
        if self.rich:
            self.rich_box = QtWidgets.QTextEdit(fetch[7])
        cursor.close()

# Методы Удаления и Изменения аккаунта
    def delete_account(self, change=True):
        """ Удаление аккаунта и соответствующей ветви в дереве """
        # Удаление с БД
        if self.mode:
            self.connect.open()
            query = QtSql.QSqlQuery()
            query.prepare(
                "DELETE FROM accounts WHERE name = (?) AND u_id = (?) and g_id = (?)")
            query.addBindValue(self.name)
            query.addBindValue(self.u_id)
            query.addBindValue(self.g_id)
            query.exec_()
            query.finish()
            self.connect.close()
        else: 
            cursor = self.connect.cursor()
            cursor.execute("DELETE FROM accounts WHERE name=\'{}\' AND u_id=\'{}\' and g_id=\'{}\'".format(
                self.name, self.u_id, self.g_id
            ))
            self.connect.commit()
            cursor.close()
        # Закрытие и удаление ветви
        self.tree.currentItem().parent().removeChild(self.tree.currentItem())
        self.dialog.close()
        self.close()
        if not change:
            successful = Message("Успех", "Аккаунт успешно удален!", self)
            successful.exec_()


    def change_account(self):
        """ Удаляем старый, создаем новый аккаунт"""
        self.delete_account(True)
        account = NewAccount(
            self.tree, self.mode, self.u_id, self.g_id, self.connect, self.key, True, self.parent(), self)
        account.show()
        self.close()
        self.dialog.close()

# Обработчики кликов
    def click_delete(self):
        """ Обработчик нажатия кнопки удаления аккаунта """
        self.dialog = Dialog(
            "Удаление", "Вы уверены, что хотите удалить\nинформацию об аккаунте?", self)
        self.dialog.accept.clicked.connect(self.delete_account)
        self.dialog.reject.clicked.connect(self.dialog.close)
        self.dialog.exec_()

    def click_change(self):
        """ Обработчик нажатия кнопки изменения аккаунта """
        self.dialog = Dialog(
            "Изменение", "Вы уверены, что хотите изменить\nинформацию об аккаунте?", self)
        self.dialog.accept.clicked.connect(self.change_account)
        self.dialog.reject.clicked.connect(self.dialog.close)
        self.dialog.exec_()