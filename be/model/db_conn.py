from sqlalchemy.dialects.postgresql import psycopg2
import psycopg2
from be.model import store


class DBConn:  #定义DBConn类
    def __init__(self):
        self.conn = psycopg2.connect(database="bookstore", user="postgres", password="shengmowang1", host="localhost", port="5432")
        # self.conn = self.conn.cursor()
    #定义user_id_exist函数
    def user_id_exist(self, user_id):
        self.cursor = self.conn.cursor()
        self.cursor.execute("SELECT user_id FROM usr WHERE user_id = '%s'" % (user_id,))
        row =self.cursor.fetchone()
        if row is None:
            return False
        else:
            return True
    #定义book_id_exist函数
    def book_id_exist(self, store_id, book_id):
        self.cursor = self.conn.cursor()
        self.cursor.execute("SELECT book_id FROM store WHERE store_id = '%s' AND book_id = '%s'" % (store_id, book_id))
        row = self.cursor.fetchone()
        if row is None:
            return False
        else:
            return True
    #定于store_id_exist函数
    def store_id_exist(self, store_id):
        self.cursor = self.conn.cursor()
        self.cursor.execute("SELECT store_id FROM user_store WHERE store_id = '%s'" % (store_id,))
        row = self.cursor.fetchone()
        if row is None:
            return False
        else:
            return True
