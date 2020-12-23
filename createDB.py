# -*- coding: utf-8 -*-
import sqlite3

def main():
    """ Создаем Базу данных """
    sql = """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            login TEXT UNIQUE
        );

        CREATE TABLE groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            u_id INTEGER,
            name TEXT UNIQUE,
            FOREIGN KEY (u_id) REFERENCES users(id)
        );

        CREATE TABLE sites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            u_id INTEGER, 
            g_id INTEGER,
            name TEXT,
            url TEXT,
            FOREIGN KEY (u_id) REFERENCES users(id)
            FOREIGN KEY (g_id) REFERENCES groups(id)
        );

        CREATE TABLE accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            u_id INTEGER, 
            g_id INTEGER, 
            s_id INTEGER,
            name TEXT,
            login TEXT, 
            passw TEXT, 
            about TEXT,
            FOREIGN KEY (u_id) REFERENCES users(id)
            FOREIGN KEY (g_id) REFERENCES groups(id)
            FOREIGN KEY (s_id) REFERENCES sites(id)
        );
        """

    con = sqlite3.connect("main.db")
    cur = con.cursor()

    try:
        cur.executescript(sql)
    except sqlite3.DatabaseError as err:
        print("Error is {}".format(err))
    else:
        print("Successfully")

    cur.close()
    con.close()

if __name__ == "createDB":
    main() 