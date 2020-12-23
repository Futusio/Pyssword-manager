from PyQt5 import QtSql
import psycopg2


class Connect():
    def __init__(self):
        pass

    @staticmethod
    def connect():
        try: # Коннект надо закинуть в главный файл
            return psycopg2.connect(
                dbname = "main",
                user = "server",
                password = "11111111",
                host = "192.168.56.102",
                port = "5432"
            )
    
        except psycopg2.OperationalError:
            return False
    