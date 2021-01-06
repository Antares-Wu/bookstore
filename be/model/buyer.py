import uuid
import json
import logging

import psycopg2

from be.model import db_conn
from be.model import error


class Buyer(db_conn.DBConn):
    def __init__(self):
        db_conn.DBConn.__init__(self)




    #定义下单函数
    # 检查user_id,store_id，在store中查询书的id，存货量，描述，价格
    # 如果存货量小于订单量，则返回错误
    # 更新存货量，stock_level - count，
    # 将订单号，书号，订单量，价格插入new_order_detail
    # 将订单号，store_id,user_id插入new_order
    def new_order(self, user_id: str, store_id: str, id_and_count: [(str, int)]) -> (int, str, str):
        order_id = ""
        try: #判断用户id和门店id是否存在
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id) + (order_id, )
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id) + (order_id, )
            uid = "{}_{}_{}".format(user_id, store_id, str(uuid.uuid1()))

            for book_id, count in id_and_count: #对每个书的id和数量
                self.cursor = self.conn.cursor()
                self.cursor.execute( #查询书的id，数量，信息，从store
                    "SELECT book_id, stock_level, book_info FROM store "
                    "WHERE store_id = '%s' AND book_id = '%s'" %
                    (store_id, book_id))  #从前端获取store_id和book_id
                row = self.cursor.fetchone()  #获取查询的信息
                if row is None:  #如果查询结果为空
                    return error.error_non_exist_book_id(book_id) + (order_id, )
                #获取书的存量和书的信息
                stock_level = row[1]
                book_info = row[2]
                #写为json
                book_info_json = json.loads(book_info)
                #从json中获取价格
                price = book_info_json.get("price")
                #如果存货量小于订单量，则返回错误
                if stock_level < count:
                    return error.error_stock_level_low(book_id) + (order_id,)
                #更新存货量，stocklevel - count
                self.cursor.execute(
                    "UPDATE store set stock_level = stock_level-%d "
                    "WHERE store_id = '%s' and book_id = '%s' and stock_level >= %d" %
                    (count, store_id, book_id, count))
                if self.cursor.rowcount == 0:
                    return error.error_stock_level_low(book_id) + (order_id, )
                #新增order（细节）
                self.cursor.execute(
                        "INSERT INTO new_order_detail(order_id, book_id, count, price) "
                        "VALUES('%s', '%s', %d, %d)" %
                        (uid, book_id, count, price))
            #新增order
            self.cursor = self.conn.cursor()
            self.cursor.execute(
                "INSERT INTO new_order(order_id, store_id, user_id) "
                "VALUES('%s', '%s', '%s')" %
                (uid, store_id, user_id))
            self.conn.commit()
            order_id = uid
        except psycopg2.errors.UniqueViolation:
            return error.error_exist_store_id(store_id)

        return 200, "ok", order_id


    #定义付款函数
    #传入参数 user_id, password, order_id

    # 在new_order中获取订单信息
    ## 查询order_id,user_id,store_id
    #验证并查询buyer的账户信息
    ## 验证buyer_id是不是相符合
    ## 查询buyer的账户信息，balance和password
    # 查询user_store表，寻找到seller的信息
    # 在new_order_detail中找到book_id,count,price, 以order_id为索引
    # 计算总价
    # 更新买家和卖家的账户余额
    # 从new_order里删除这个order
    # 从new_order_detail中删除

    def payment(self, user_id: str, password: str, order_id: str) -> (int, str):
        try:#查询订单信息中的值
            #查询order_id, user_id, store_id
            self.cursor = self.conn.cursor()
            self.cursor.execute("SELECT order_id, user_id, store_id FROM new_order WHERE order_id = '%s'" % (order_id,))
            row = self.cursor.fetchone()
            if row is None:
                return error.error_invalid_order_id(order_id)

            order_id = row[0]
            buyer_id = row[1]
            store_id = row[2]
            #验证buyer_id是不是相符合
            if buyer_id != user_id:
                return error.error_authorization_fail()
            #查询buyer的账户信息，balance和password
            self.cursor.execute("SELECT balance, password FROM usr WHERE user_id = '%s'" % (buyer_id,))

            row = self.cursor.fetchone()
            if row is None:
                return error.error_non_exist_user_id(buyer_id)
            balance = row[0]
            #验证password是不是相符合
            if password != row[1]:
                return error.error_authorization_fail()
            #查询user_store表，寻找到store_id和user_id的对应关系
            self.cursor.execute("SELECT store_id, user_id FROM user_store WHERE store_id = '%s'" % (store_id,))
            row = self.cursor.fetchone()
            #如果store不存在，就返回store不存在的错误
            if row is None:
                return error.error_non_exist_store_id(store_id)
            #即找到seller_id
            seller_id = row[1]
            #如果seller_id不存在，则返回seller_id不存在的错误
            if not self.user_id_exist(seller_id):
                return error.error_non_exist_user_id(seller_id)
            #在new_order_detail中找到book_id,count,price, 以order_id为索引
            self.cursor.execute("SELECT book_id, count, price FROM new_order_detail WHERE order_id = '%s'" % (order_id,))
            cursor = self.cursor.fetchall()
            total_price = 0
            #计算总价
            for row in cursor:
                count = row[1]
                price = row[2]
                total_price = total_price + price * count
            #如果账户余额小于总价，返回not_sufficent_funds错误
            if balance < total_price:
                return error.error_not_sufficient_funds(order_id)
            #更新用户的账户余额
            self.cursor.execute("UPDATE usr set balance = balance - %d" 
                                  "WHERE user_id = '%s' AND balance >= %d" %
                                  (total_price, buyer_id, total_price))
            #再次检查，如果账户余额小于总价，则返回not_sufficent_funds错误
            if self.cursor.rowcount == 0:
                return error.error_not_sufficient_funds(order_id)
            #更新卖家的账户余额
            self.cursor.execute("UPDATE usr set balance = balance+%d"
                                  "WHERE user_id = '%s'" %
                                  (total_price, seller_id)) ##
            #检查id是否存在
            if self.cursor.rowcount == 0:
                return error.error_non_exist_user_id(seller_id)
            #从new_order里删除这个order
            self.cursor.execute("DELETE FROM new_order WHERE order_id = '%s'" % (order_id, ))
            if self.cursor.rowcount == 0:
                return error.error_invalid_order_id(order_id)
            #从new_order_detail中删除
            self.cursor.execute("DELETE FROM new_order_detail where order_id = '%s'" % (order_id, ))
            if self.cursor.rowcount == 0:
                return error.error_invalid_order_id(order_id)

            self.conn.commit()
        except psycopg2.errors.UniqueViolation:
            return error.error_exist_user_id(user_id)

        return 200, "ok"



    # 充值函数
    # 传入三个参数，user_id, password, add_value

    # 检验用户信息，在usr中增加用户的balance
    def add_funds(self, user_id, password, add_value) -> (int, str):
        try:
            self.cursor = self.conn.cursor()
            self.cursor.execute("SELECT password  from usr where user_id='%s'" % (user_id,))
            row = self.cursor.fetchone()
            #先检验查询是不是空值
            if row is None:
                return error.error_authorization_fail()

            #再检验密码是不是正确
            if row[0] != password:
                return error.error_authorization_fail()
            #增加用户的balance
            self.cursor.execute(
                "UPDATE usr SET balance = balance + %d WHERE user_id = '%s'" %
                (add_value, user_id))
            #检查cursor.rowcount的行数是不是零
            if self.cursor.rowcount == 0:
                return error.error_non_exist_user_id(user_id)

            self.conn.commit()
        except psycopg2.errors.UniqueViolation:
            return error.error_exist_user_id(user_id)

        return 200, "ok"
