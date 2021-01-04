import logging
import os
import sqlite3 as sqlite
import sqlalchemy
from sqlalchemy.dialects.postgresql import psycopg2
import psycopg2

class Store:
    database: str
    #添加数据库be.db
    #初始化表
    def __init__(self, db_path):
       # self.database = os.path.join(db_path, "be.db")
        self.init_tables()

    def init_tables(self):
        try:
            conn = psycopg2.connect(database="bookstore", user="postgres", password="shengmowang1",
                                    host="localhost", port="5432")
            conn = conn.cursor()
            # conn = self.get_db_conn()
            #创建user表，四个属性
            #user_id 文本，主键
            #password 文本
            #balance 整数
            #token 文本
            #terminal 文本
            conn.execute(
                "CREATE TABLE IF NOT EXISTS usr ("
                "user_id TEXT PRIMARY KEY, password TEXT NOT NULL, "
                "balance INTEGER NOT NULL, token TEXT, terminal TEXT);"
            )
            #创建user_store表，有两个属性
            #user_id 文本
            #store_id
            #主键是（user_id,store_id）
            conn.execute(
                "CREATE TABLE IF NOT EXISTS user_store("
                "user_id TEXT, store_id, PRIMARY KEY(user_id, store_id));"
            )
            #创建store表，有四个属性
            #store_id 文本
            #book_id 文本
            #book_info 文本
            #stock_level 整数
            #主键（store_id, book_id）
            conn.execute(
                "CREATE TABLE IF NOT EXISTS store( "
                "store_id TEXT, book_id TEXT, book_info TEXT, stock_level INTEGER,"
                " PRIMARY KEY(store_id, book_id));"
            )
            #创建new_order表，有三个属性
            #order_id 文本 主键
            #user_id 文本
            #store_id 文本
            #
            conn.execute(
                "CREATE TABLE IF NOT EXISTS new_order( "
                "order_id TEXT PRIMARY KEY, user_id TEXT, store_id TEXT);"
            )
            #创建new_order_detail表 有三个属性
            #order_id 文本
            #book_id 文本
            #count 整数
            #price 整数
            #主键 （order_id , book_id ）
            conn.execute(
                "CREATE TABLE IF NOT EXISTS new_order_detail( "
                "order_id TEXT, book_id TEXT, count INTEGER, price INTEGER,  "
                "PRIMARY KEY(order_id, book_id));"
            )

            conn.commit()
        except sqlalchemy.exc.IntegrityError:
            conn.rollback()

#     def get_db_conn(self) -> sqlite.Connection:
#         return sqlite.connect(self.database)
#
#
# database_instance: Store = None
#
#
# def init_database(db_path):
#     global database_instance
#     database_instance = Store(db_path)
#
#
# def get_db_conn():
#     global database_instance
#     return database_instance.get_db_conn()
