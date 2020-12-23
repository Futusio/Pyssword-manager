from PyQt5 import QtWidgets, QtSql, QtCore, QtGui
from psycopg2 import sql
from groups import GroupWindow
from connect import Connect
from message import Message

groups = [] # Переписать на словарь! 

class GroupButton(QtWidgets.QPushButton):
    """ Расширение QPushButton в целях 
    отслеживания идентификаторов кнопок """
    clicked = QtCore.pyqtSignal(str, object)

    def __init__(self, title, u_id, g_id, parent=None):
        super().__init__(parent)
        self.u_id = u_id
        self.g_id = g_id
        self.title = title # Имя кнопки
        self.parent = parent
        self.setObjectName(title)
        self.setText(title)

    def mousePressEvent(self, event):
        """ Новому окну будет передан идентификатор и соединение с БД """
        self.group = GroupWindow(self.title, self.parent.mode, self.u_id, self.g_id, self.parent.key, self.parent.conn, self)
        self.group.show()

class NewGroup(QtWidgets.QWidget):
    """ Виджет для создания новых груп"""
    def __init__(self, parent=None):
        super().__init__(parent, QtCore.Qt.Window)
        # Настройки окна
        self.setFixedSize(225,100)
        self.setWindowFlags(
            QtCore.Qt.Window | 
            QtCore.Qt.WindowCloseButtonHint
            )
        self.setWindowModality(QtCore.Qt.ApplicationModal) # Block Parent Window
        self.setWindowTitle("Новая группа")
        self.initUi()
        # Event
        self.okBtn.clicked.connect(self.on_clicked)
    
    def initUi(self): # Переписать и упорядочить 
        self.widget = QtWidgets.QWidget()
        self.textBox = QtWidgets.QLineEdit()
        self.textBox.setPlaceholderText("Ex.: Mail")

        self.okBtn = QtWidgets.QPushButton("Ок") 
        self.label = QtWidgets.QLabel("Введите название:")
        vBox  = QtWidgets.QVBoxLayout()
        hBox = QtWidgets.QHBoxLayout()

        hBox.addWidget(self.label)
        hBox.addWidget(self.textBox)
        self.widget.setLayout(hBox)
        vBox.addWidget(self.widget)
        vBox.addWidget(self.okBtn)

        self.setLayout(vBox)

    def checked_textBox(self):
        """ Проверка вводимого значения """
        if self.textBox.text() == "":
            return "Имя группы не должно быть пустым!" 
        elif self.textBox.text().title() in groups or self.textBox.text() in groups:
            return "Имя группы должно быть уникальным!"
        else: return True

    def local(self):
        """ Создание записи в локальной БД """
        if self.parent().conn.open(): # В дальнейшем переместить SQL коды в другой модуль
            query = QtSql.QSqlQuery() # Возможно, нужно дописать проверку расширения таблицы
            query.prepare("INSERT INTO groups VALUES (NULL, ?, ?)")
            query.addBindValue(self.parent().u_id)
            query.addBindValue(self.textBox.text().title())
            if query.exec_(): 
                successful = Message("Успех","Новая группа успешно создана!", self)
                successful.exec_()
                query.finish()
            else: 
                error = Message("Ошибка","Неизвестная ошибка!\nПерезагрузите приложение", self)
                error.exec_()
            query.finish()
            query.exec("SELECT * FROM groups WHERE name = \'{}\' and u_id = \'{}\'".format(
                self.textBox.text().title(), self.parent().u_id))
            query.first()
            self.close()
            # А дальше добавляем виджет
            self.parent().buttonLayout.addWidget(
                GroupButton(self.textBox.text().title(),
                            self.parent().u_id, query.value('id'), self.parent())) # Добавление новой кнопки
            groups.append(self.textBox.text().title())
            self.parent().buttonLayout.setAlignment(QtCore.Qt.AlignTop)
            self.parent().conn.close()
            query.finish()
        else:
            error = Message("Ошибка","Ошибка подключения к Базе данных\nПопробуйте снова", self)
            error.exec_()
        self.textBox.setText("")

    def remote(self):
        # Добавление в БД 
        cur = self.parent().conn.cursor()
        query = sql.SQL('INSERT INTO groups (u_id, name) VALUES (\'{}\', \'{}\')'.format(
            self.parent().u_id, self.textBox.text().title()
        ))
        cur.execute(query)
        self.parent().conn.commit()
        msg = Message("Успех","Группа успешно добавлена!", self)
        msg.exec_()
        # Вытаскиваем новый g_id
        cur.execute("SELECT * FROM groups WHERE name = \'{}\'".format(self.textBox.text().title()))
        groups.append(self.textBox.text().title())
        # Виджет 
        self.parent().buttonLayout.addWidget(
            GroupButton(self.textBox.text().title(),
                        self.parent().u_id, cur.fetchall()[0][0], self.parent())) # Добавление новой кнопки
        self.parent().buttonLayout.setAlignment(QtCore.Qt.AlignTop)
        self.close()
        self.textBox.setText("")
        cur.close()

    def on_clicked(self):
        """ Надо дописать обработку ошибок
        точнее сообщения об ошибках"""
        if self.checked_textBox() == True: # Проверка валидности ввода 
            if self.parent().mode: self.local() # Выбор БД 
            else: self.remote()
        else: # Вывод результатов ошибки в отдельное окно
            self.error = Message("Ошибка","{}".format(self.checked_textBox()), self)
            self.error.exec_()
            self.textBox.setText("")

class Scroll(QtWidgets.QMainWindow):
    """ Главное окошко программы """ 
    def __init__(self, mode, u_id, key, conn = None, parent=None):
        super().__init__(parent)
        # Variables
        self.key = key
        self.u_id = u_id
        self.conn = conn
        self.mode = mode # local or remote
        # Settings 
        self.add = None # The object will apear later
        self.setWindowTitle("PYssword Manager")
        self.setWindowFlags(
            QtCore.Qt.Window | 
            QtCore.Qt.WindowCloseButtonHint | 
            QtCore.Qt.MSWindowsFixedSizeDialogHint)
        self.setMinimumHeight(400)
        self.initUi()
        # Fill widget 
        if self.mode: self.fill_widget_local()
        else: self.fill_widget_remote()
        # Events 
        self.addGroup.clicked.connect(self.on_clicked)

    def initUi(self):
        """ Инициализация окна """ 
        self.setWindowIcon(QtGui.QIcon("icon.ico"))
        central = QtWidgets.QWidget() # Сюда накидываем виджиты 
        container = QtWidgets.QWidget() # Это прикрепляем к скролу 
        self.buttonLayout = QtWidgets.QVBoxLayout() # Крепим к контейнеру 
        container.setLayout(self.buttonLayout) # Наполняем в fill_widget 
        # Ох сколько ведер пота ты тут оставил
        scroll = QtWidgets.QScrollArea()
        scroll.setWidget(container)
        # Надстройка 
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scroll.setWidgetResizable(True)
        # Наполняем слой 
        vLayout = QtWidgets.QVBoxLayout(central)
        vLayout.addWidget(scroll)
        self.addGroup = QtWidgets.QPushButton("Добавить группу")
        vLayout.addWidget(self.addGroup)
        # Перебрасываем слой на виджет и делаем главным
        central.setLayout(vLayout)
        self.setCentralWidget(central)

    def fill_widget_local(self):
        """ В случае выбора локальной БД """
        self.conn.open()
        query = QtSql.QSqlQuery()
        query.prepare("select * from groups where u_id = (?) order by id")
        query.addBindValue(self.u_id)
        query.exec_()
        # Проходим по всем записям таблицы и формируем список групп 
        if query.isActive():
            query.first() # Перепишу если найду итератор query
            while query.isValid():
                if query.value('u_id') == self.u_id:
                    btn1 = GroupButton(query.value('name'), self.u_id, query.value('id'), self)
                    groups.append(query.value('name').title())
                    self.buttonLayout.addWidget(btn1)
                    self.buttonLayout.setAlignment(QtCore.Qt.AlignTop)
                    query.next()  
        # Закрываем соединение 
        query.finish()
        self.conn.close()
    
    def fill_widget_remote(self):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM groups WHERE u_id = \'{}\'".format(self.u_id))
        for fetch in cur.fetchall():
            btn = GroupButton(fetch[2], self.u_id, fetch[0], self)
            groups.append(fetch[2].title())
            self.buttonLayout.addWidget(btn)
            self.buttonLayout.setAlignment(QtCore.Qt.AlignTop)
        cur.close()

    def on_clicked(self):
        """ Добавление новой группы """
        if not self.add:
            self.add = NewGroup(self)
        self.add.show()