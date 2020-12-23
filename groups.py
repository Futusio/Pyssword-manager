from PyQt5 import QtWidgets, QtCore, QtSql, QtGui
from accounts import NewAccount, Account
from message import Message, Dialog
from psycopg2 import sql


class GroupWindow(QtWidgets.QMainWindow):
    """В этом окне будут отображаться непосредственно
    сайты и аккаунты привязанные к этим сайтам"""
    def __init__(self, name, mode, u_id, g_id, key, conn, button, parent=None):
        super().__init__(parent)
        # Variables
        self.key = key
        self.button = button
        self.name = name
        self.mode = mode
        self.g_id = g_id
        self.u_id = u_id
        self.conn = conn
        self.new_site = None
        # Fill widget
        self.initUi()
        if mode: self.local()
        else: self.remote()
        # Events 
        self.tree.doubleClicked.connect(self.tree_click)
        self.btn.clicked.connect(self.newSite)
        self.delete_group.clicked.connect(self.delete_group_click)

    def initUi(self):
        self.setWindowIcon(QtGui.QIcon("icon.ico"))
        # Settings 
        central = QtWidgets.QWidget()
        self.setWindowTitle("Группа: {}".format(self.name))
        layout = QtWidgets.QVBoxLayout()
        # Widgets 
        self.tree = QtWidgets.QTreeWidget()
        self.tree.setHeaderLabel(self.name)
        self.btn = QtWidgets.QPushButton("Новый сайт")
        self.delete_group = QtWidgets.QPushButton("Удалить группу")
        # Fill the layout 
        layout.addWidget(self.tree)
        layout.addWidget(self.btn)
        layout.addWidget(self.delete_group)
        central.setLayout(layout)
        self.setCentralWidget(central)

    def tree_click(self):
        if self.tree.currentItem().text(0) == "Добавить":
            # Окно добавления аккаунту 
            account = NewAccount(self.tree, self.mode, self.u_id, self.g_id, self.conn, self.key, parent=self)
            account.show()
        elif self.tree.currentItem().parent() is None:
            # Окно информации о сайте
            site = Site(self)
            site.show()
        else: 
            # Окно информации об аккаунте 
            info = Account(self.tree, self.mode, self.u_id, self.g_id, self.conn, self.key, parent=self)
            info.show()

    def local(self):
        """ Метод заполненния виджета из локальной БД """
        # Вытаскиваем список сайтов 
        self.conn.open()
        query = QtSql.QSqlQuery()
        query.prepare("SELECT * FROM sites WHERE u_id = (?) AND g_id = (?) order by id")
        query.addBindValue(self.u_id)
        query.addBindValue(self.g_id)
        if query.exec_(): # Попытка выполнить запрос 
            query.first() # Переписать если найду итератор query 
            while query.isValid():
                # Запрос на получение s_id для каждой ветви
                s_id_query = QtSql.QSqlQuery()
                s_id_query.exec(
                    "SELECT id FROM sites WHERE name = \"{}\" AND g_id =\"{}\"".format(
                        query.value("name"), self.g_id))
                s_id_query.first()
                s_id = s_id_query.value("id")
                s_id_query.finish() 
                # После получения s_id 
                if query.value("g_id") == self.g_id:
                    s_query = QtSql.QSqlQuery()
                    s_query.exec("SELECT name FROM accounts WHERE s_id = \"{}\"".format(s_id))
                    if s_query.isActive():
                        s_query.first()
                        node = QtWidgets.QTreeWidgetItem(self.tree, [query.value("name"), ])
                        while s_query.isValid():
                            node.addChild(QtWidgets.QTreeWidgetItem([s_query.value("name")]))
                            s_query.next()
                        node.addChild(QtWidgets.QTreeWidgetItem(["Добавить"]))
                query.next()
        else: 
            Message("Ошибка","Неизвестная ошибка!\nПерезагрузите приложение", self).exec_()
        query.finish()
        self.conn.close()

    def remote(self):
        """ Заполнение Виджета из удаленной БД """
        cursor = self.conn.cursor()
        query = sql.SQL("""
                SELECT * FROM sites WHERE u_id = \'{}\' AND g_id = \'{}\'""".format(
                    self.u_id, self.g_id
                    ))
        if cursor.execute(query) is None: # Проверка успешности выполнения запроса
            for fetch in cursor.fetchall(): # Заполнение Сайтов 
                q_query = sql.SQL("""
                    SELECT * FROM accounts WHERE s_id =\'{}\'""".format(
                        fetch[0]
                ))
                cursor.execute(q_query)
                node = QtWidgets.QTreeWidgetItem(self.tree, [fetch[3]])
                for fetch    in cursor.fetchall(): # Заполнение аккаунтов 
                    node.addChild(QtWidgets.QTreeWidgetItem([fetch[4]]))
                node.addChild(QtWidgets.QTreeWidgetItem(["Добавить"]))
        else: Message("Ошибка", "Неизвестная ошибка!\nПерезагрузите приложение", self).exec_()
        cursor.close()

    def delete(self):
        """ Метод удаление группы и всех привязанных 
        сайтов и аккаунтов """
        if self.mode: # Очищение локальной БД 
            self.conn.open()
            group_query, sites_query, account_query = QtSql.QSqlQuery(), QtSql.QSqlQuery(), QtSql.QSqlQuery()
            group_query.prepare("DELETE FROM groups WHERE id = (?)")
            sites_query.prepare("DELETE FROM sites WHERE g_id = (?)")
            account_query.prepare("DELETE FROM accounts WHERE g_id = (?)")
            group_query.addBindValue(self.g_id)
            sites_query.addBindValue(self.g_id)
            account_query.addBindValue(self.g_id)
            self.dialog.close()
            if group_query.exec_() and sites_query.exec_() and account_query.exec_():
                Message("Успех", "Информация о группе, ее сайтах и аккаунтах\nбыла успешно удалена", self).exec_()
            else: 
                Message("Ошибка","Неизвестная ошибка. Перезагрузите приложение", self).exec_()
            group_query.finish()
            sites_query.finish()
            account_query.finish()
            self.conn.close()
        else: # Чистка удаленной БД
            cursor = self.conn.cursor()
            group_query = sql.SQL("DELETE FROM groups WHERE id = \'{}\'".format(self.g_id))
            sites_query = sql.SQL("DELETE FROM sites WHERE g_id = \'{}\'".format(self.g_id))
            account_query = sql.SQL("DELETE FROM accounts WHERE g_id = \'{}\'".format(self.g_id))
            cursor.execute(account_query)
            cursor.execute(sites_query)
            cursor.execute(group_query)
            self.conn.commit()
            cursor.close()
            self.dialog.close()
            Message("Успех","Информация о группе, ее сайтах и аккаунтах\nБыла успешно удалена", self).exec_()
        self.close()
        self.button.deleteLater()

    def delete_group_click(self):
        self.dialog = Dialog(
            "Удаление", "Вы уверены, что хотите удалить группу\nИ все привязанные аккаунты?", self)
        self.dialog.accept.clicked.connect(self.delete)
        self.dialog.reject.clicked.connect(self.dialog.close)
        self.dialog.exec_()

    def newSite(self):
        """Создает окошко добавления сайта """
        if not self.new_site:
            self.new_site = NewSite(self)
        self.new_site.show()

class Site(QtWidgets.QWidget):
    """ Окно для удаления или изменения данных
    о сайте и всех прикрепленных аккаунтов """
    def __init__(self, parent=None):
        super().__init__(parent, QtCore.Qt.Window)
        if self.parent().mode: self.get_variables_local()
        else: self.get_variables_remote()
        self.initUi()
        # Обработчик 
        self.ok_btn.clicked.connect(self.change_site_click)
        self.del_btn.clicked.connect(self.delete_site_click)

# GET VARIABLES
    def get_variables_remote(self):
        """ Вычисление значений полей из удаленной БД """
        cursor = self.parent().conn.cursor()
        query = sql.SQL("""
                SELECT * FROM sites WHERE u _id=\'{}\' AND g_id=\'{}\' AND name=\'{}\'""".format(
                    self.parent().u_id, self.parent().g_id, self.parent().tree.currentItem().text(0)
                ))
        if cursor.execute(query) is None:
            fetch = cursor.fetchone()
            self.id = fetch[0]
            self.name = fetch[3]
            self.url = fetch[4]
        else: Message("Ошибка", "Неизвестная ошибка!\nПерезагрузите приложение", self).exec_()
        cursor.close()

    def get_variables_local(self):
        """ Данный метод вычисляет значение полей класса
        А именно name Сайта и его URL """
        self.parent().conn.open()
        query = QtSql.QSqlQuery()
        query.prepare("""SELECT * FROM sites
                WHERE u_id = (?) AND g_id = (?) AND name = (?)""")
        query.addBindValue(self.parent().u_id)
        query.addBindValue(self.parent().g_id)
        query.addBindValue(self.parent().tree.currentItem().text(0))
        query.exec_()
        query.first()
        self.id = query.value('id')
        self.name = query.value('name')
        self.url = query.value('url')
        query.finish()
        self.parent().conn.close()

    def initUi(self):
        # Настройки окна
        self.setWindowTitle("Править: {}".format(self.name))
        self.setWindowFlags(
            QtCore.Qt.Window | 
            QtCore.Qt.WindowCloseButtonHint | 
            QtCore.Qt.MSWindowsFixedSizeDialogHint)
        self.setWindowModality(QtCore.Qt.ApplicationModal) # Block Parent Window
        # Создание виджетов
        label_1 = QtWidgets.QLabel("Название:")
        label_2 = QtWidgets.QLabel("Ссылка:")
        self.textbox_1 = QtWidgets.QLineEdit(self.name)
        self.textbox_1.setPlaceholderText("Прим.: Вконтакте")
        self.textbox_1.setMaxLength(20)
        self.textbox_2 = QtWidgets.QLineEdit(self.url)
        self.textbox_2.setPlaceholderText("Необязательно")
        self.ok_btn = QtWidgets.QPushButton("Сохранить")
        self.del_btn = QtWidgets.QPushButton("Удалить")
        # Создание слоев 
        grid = QtWidgets.QGridLayout()
        grid.addWidget(label_1, 0,0)
        grid.addWidget(label_2, 1,0)
        grid.addWidget(self.textbox_1, 0,1)
        grid.addWidget(self.textbox_2, 1,1)
        grid.addWidget(self.del_btn, 3,0)
        grid.addWidget(self.ok_btn, 3,1)
        self.setLayout(grid)

# EVENTS 
    def delete_site(self):
        """ Метод удаляет из БД сайт, все аккаунты,
        а так же очищает дерево """ 
        # Удаление из Базы данных
        if self.parent().mode: # Удаление из Локальной БД
            self.parent().conn.open()
            query, q_query = QtSql.QSqlQuery(), QtSql.QSqlQuery()
            query.prepare("DELETE FROM sites WHERE id = (?)")
            q_query.prepare("DELETE FROM accounts WHERE s_id = (?)")
            query.addBindValue(self.id)
            q_query.addBindValue(self.id)
            query.exec_()
            q_query.exec_()
            query.finish()
            q_query.finish()
        else: # Удаление из удаленной БД
            cursor = self.parent().conn.cursor()
            query = sql.SQL("DELETE FROM sites WHERE id = \'{}\'".format(self.id))
            q_query = sql.SQL("DELETE FROM accounts WHERE s_id = \'{}\'".format(self.id))
            cursor.execute(q_query)
            cursor.execute(query)
            self.parent().conn.commit()
            cursor.close()
        # Удаление из дерева и закрываем окна 
        self.parent().tree.currentItem().removeChild(self.parent().tree.currentItem())
        self.dialog.close()
        self.close()
        Message("Успех","Данные успешно удалены", self).exec_()

    def change_site(self):
        """ Метод изменяет данные в БД,
        а так же изменяет название деревца """
        if self.parent().mode: # Изменяем локальную БД
            self.parent().conn.open()
            query = QtSql.QSqlQuery()
            query.prepare("UPDATE sites SET name = (?), url = (?) WHERE id = (?)")
            query.addBindValue(self.textbox_1.text())
            query.addBindValue(self.textbox_2.text())
            query.addBindValue(self.id)
            query.exec_()
            query.finish()
            self.parent().conn.close()
        else: # Изменение удаленной БД 
            cursor = self.parent().conn.cursor()
            query = sql.SQL("UPDATE sites SET name=\'{}\', url=\'{}\' WHERE id=\'{}\'".format(
                self.textbox_1.text(), self.textbox_2.text(), self.id)
            )
            cursor.execute(query)
            self.parent().conn.commit()
            cursor.close()
        # Изменяем дерево и закрываем окна
        self.parent().tree.currentItem().setText(0, self.textbox_1.text())
        self.dialog.close()  
        self.close()      
        Message("Успех","Изменения успешно сохранены", self).exec_()

    def delete_site_click(self):
        self.dialog = Dialog(
            "Удаление", "Вы уверены, что хотите удалить сайт из списка\nИ все его аккаунты?", self)
        self.dialog.accept.clicked.connect(self.delete_site)
        self.dialog.reject.clicked.connect(self.dialog.close)
        self.dialog.exec_()

    def change_site_click(self):
        if self.textbox_1.text() == self.name and self.textbox_2.text() == self.url:
            self.close()
        else:
            self.dialog = Dialog(
                "Изменение", "Вы уверены, что хотите изменить\nинформацию о сайте?", self)
            self.dialog.accept.clicked.connect(self.change_site)
            self.dialog.reject.clicked.connect(self.dialog.close)
            self.dialog.exec_()

class NewSite(QtWidgets.QWidget):
    """ Окно для добавления сайтов в 
    таблицу .sites """
    def __init__(self, parent=None):
        super().__init__(parent, QtCore.Qt.Window)
        self.initUi()
        # Обработчик 
        self.btn.clicked.connect(self.on_clicked)

    def initUi(self):
        # Настройки окна
        self.setWindowTitle("Добавить сайт")
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.MSWindowsFixedSizeDialogHint)
        self.setWindowModality(QtCore.Qt.ApplicationModal) # Block Parent Window
        # Создание виджетов
        label_1 = QtWidgets.QLabel("Введите название:")
        label_2 = QtWidgets.QLabel("Ссылка на ресурс:")
        self.textbox_1 = QtWidgets.QLineEdit()
        self.textbox_1.setPlaceholderText("Прим.: Вконтакте")
        self.textbox_1.setMaxLength(20)
        self.textbox_2 = QtWidgets.QLineEdit()
        self.textbox_2.setPlaceholderText("Необязательно")
        self.btn = QtWidgets.QPushButton("добавить")
        # Создание слоев 
        grid = QtWidgets.QGridLayout()
        grid.addWidget(label_1, 0,0)
        grid.addWidget(label_2, 1,0)
        grid.addWidget(self.textbox_1, 0,1)
        grid.addWidget(self.textbox_2, 1,1)
        grid.addWidget(self.btn, 3,0,1,2)
        self.setLayout(grid)

    def local(self):
        """ Локальная БД """
        self.parent().conn.open()
        query = QtSql.QSqlQuery()
        # Формирование запроса
        query.prepare("INSERT INTO sites VALUES (NULL, ?, ?, ?, ?)")
        query.addBindValue(self.parent().u_id)
        query.addBindValue(self.parent().g_id)
        query.addBindValue(self.textbox_1.text())
        query.addBindValue(self.textbox_2.text())
        # Проверка успешного выполнения запроса
        if query.exec_():
            Message("Успех","Новый сайт успешно добавлен!", self).exec_()
            site = QtWidgets.QTreeWidgetItem(self.parent().tree, [self.textbox_1.text()])
            site.addChild(QtWidgets.QTreeWidgetItem(["Добавить"]))
        else: 
            Message("Ошибка","Неизвестная ошибка!\nПерезагрузите приложение", self).exec_()
        query.finish()
        self.parent().conn.close()
        # Изменения виджетов
        self.close()

    def remote(self):
        """ Метод заполнения удаленной БД """
        cursor = self.parent().conn.cursor()
        query = sql.SQL("""
                   INSERT INTO sites (u_id, g_id, name, url) VALUES (\'{}\', \'{}\', \'{}\', \'{}\')""".format(
                       self.parent().u_id, self.parent().g_id, self.textbox_1.text(), self.textbox_2.text()
                   ))
        if cursor.execute(query) is None:
            self.parent().conn.commit()
            cursor.close()
            Message("Успех", "Новый сайт успешно добавлен!", self).exec_()
            site = QtWidgets.QTreeWidgetItem(self.parent().tree, [self.textbox_1.text()])
            site.addChild(QtWidgets.QTreeWidgetItem(["Добавить"]))
        else: Message("Ошибка","Неизвестная ошибка!\nПерезагрузите приложение", self).exec_()
        self.close()

    def on_clicked(self): # Добавить проверку ввалидности ввода
        """ Выбор БД"""
        if self.parent().mode: self.local()
        else: self.remote()
        self.textbox_1.setText("")
        self.textbox_2.setText("")