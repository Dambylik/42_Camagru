"""Parameterized SQL, with one connection per request (PHP equivalent: PDO)."""
import os
import pymysql


def connect():
    return pymysql.connect(
        host=os.environ.get('DB_HOST', 'db'),
        database=os.environ.get('DB_NAME', 'camagru'),
        user=os.environ['DB_USER'], password=os.environ['DB_PASSWORD'],
        charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=5, read_timeout=10, write_timeout=10,
        autocommit=False,
    )


class Database:
    def __init__(self, connection):
        self.connection = connection

    def all(self, sql, values=()):
        with self.connection.cursor() as cursor:
            cursor.execute(sql, values)
            return cursor.fetchall()

    def one(self, sql, values=()):
        rows = self.all(sql, values)
        return rows[0] if rows else None

    def execute(self, sql, values=()):
        with self.connection.cursor() as cursor:
            cursor.execute(sql, values)
            return cursor.lastrowid, cursor.rowcount
