import sqlite3 as sqlite

import psycopg2

from be.model import error
from be.model import db_conn

#定义卖家函数
class Seller(db_conn.DBConn):
    #连接数据库
    def __init__(self):
        db_conn.DBConn.__init__(self)

    #定义增加书的函数
    #传入五个参数 user_id, store_id, book_id, book_json_str, stock_level
    def add_book(self, user_id: str, store_id: str, book_id: str, book_json_str: str, stock_level: int):
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)
            if self.book_id_exist(store_id, book_id):
                return error.error_exist_book_id(book_id)
        #将书的信息插入商店
            self.cursor = self.conn.cursor()
            self.cursor.execute("INSERT into store(store_id, book_id, book_info, stock_level)"
                              "VALUES ('%s', '%s', '%s',%d)" % (store_id, book_id, book_json_str, stock_level))
            self.conn.commit()
        except psycopg2.errors.UniqueViolation:
            return error.error_exist_book_id(book_id)
        # except BaseException as e:
        #     return 530, "{}".format(str(e))
        return 200, "ok"
    #定义增加书的存货的函数
    #传入4个参数，user_id, store_id, book_id, add_stock_level
    def add_stock_level(self, user_id: str, store_id: str, book_id: str, add_stock_level: int):
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)
            if not self.book_id_exist(store_id, book_id):
                return error.error_non_exist_book_id(book_id)
        #将stock_level的值变成stock_level+add_store_level
            self.cursor = self.conn.cursor()
            self.cursor.execute("UPDATE store SET stock_level = stock_level + %d "
                              "WHERE store_id = '%s' AND book_id = '%s'" % (add_stock_level, store_id, book_id))
            self.conn.commit()
        except psycopg2.errors.UniqueViolation:
            return error.error_exist_book_id(book_id)
        return 200, "ok"
    #定义创建商店函数
    #传入两个参数 user_id, store_id
    def create_store(self, user_id: str, store_id: str) -> (int, str):
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if self.store_id_exist(store_id):
                return error.error_exist_store_id(store_id)
            #将store_id,user_id插入user_store
            self.cursor = self.conn.cursor()
            self.cursor.execute("INSERT into user_store(store_id, user_id)"
                              "VALUES ('%s', '%s')" % (store_id, user_id))
            self.conn.commit()
        except psycopg2.errors.UniqueViolation:
            return error.error_exist_store_id(store_id)
        # except BaseException as e:
        #     return 530, "{}".format(str(e))
        return 200, "ok"
