import jwt
import time
import logging

import psycopg2

from be.model import error
from be.model import db_conn

# encode a json string like:
#   {
#       "user_id": [user name],
#       "terminal": [terminal code],
#       "timestamp": [ts]} to a JWT
#   }

#定义json web token生成函数
def jwt_encode(user_id: str, terminal: str) -> str:
    encoded = jwt.encode(
        {"user_id": user_id, "terminal": terminal, "timestamp": time.time()},
        key=user_id,
        algorithm="HS256"
    )
    print(encoded)
    return encoded.decode("utf-8")


# decode a JWT to a json string like:
#   {
#       "user_id": [user name],
#       "terminal": [terminal code],
#       "timestamp": [ts]} to a JWT
#   }

#定义jwt解码函数
def jwt_decode(encoded_token, user_id: str) -> str:
    decoded = jwt.decode(encoded_token, key=user_id, algorithms="HS256")
    return decoded

#定义用户类
class User(db_conn.DBConn):
    token_lifetime: int = 3600  # 3600 second

    def __init__(self):
        db_conn.DBConn.__init__(self)
    #定义检查token函数
    def __check_token(self, user_id, db_token, token) -> bool:
        try:
            if db_token != token:
                return False
            jwt_text = jwt_decode(encoded_token=token, user_id=user_id)
            ts = jwt_text["timestamp"]
            if ts is not None:
                now = time.time()
                if self.token_lifetime > now - ts >= 0:
                    return True
        except jwt.exceptions.InvalidSignatureError as e:
            logging.error(str(e))
            return False
    #定义注册函数
    #得到用户的用户名，密码之后，获取用户的终端类型，然后生成用户的token（令牌），在usr中插入用户信息
    def register(self, user_id: str, password: str):
        try:
            terminal = "terminal_{}".format(str(time.time()))
            token = jwt_encode(user_id, terminal)
            self.cursor = self.conn.cursor()
            self.cursor.execute(
                "INSERT into usr (user_id, password, balance, token, terminal) VALUES ('%s', '%s', 0, '%s', '%s')"
                % (user_id, password, token, terminal))
            # "INSERT INTO usr (user_id, password, balance, token, terminal) values (:user_id, :password, 0, :token, :terminal)", {
            #     "user_id": user_id, "password": password, "token": token, "terminal": terminal}
            # cursor.execute("insert into weapons (user_id,weapon_id) values (%s,%s)" % (user_id, weapon_id))
            self.conn.commit()
        except psycopg2.errors.UniqueViolation:
            return error.error_exist_user_id(user_id)
        return 200, "ok"

    def check_token(self, user_id: str, token: str) -> (int, str):
        self.cursor = self.conn.cursor()
        self.cursor.execute("SELECT token from usr where user_id= '%s'" % (user_id))
        row = self.cursor.fetchone()
        if row is None:
            return error.error_authorization_fail()
        db_token = row[0]
        if not self.__check_token(user_id, db_token, token):
            return error.error_authorization_fail()
        return 200, "ok"

    def check_password(self, user_id: str, password: str) -> (int, str):
        self.cursor = self.conn.cursor()
        self.cursor.execute("SELECT password from usr where user_id= '%s'" % (user_id))
        row = self.cursor.fetchone()
        if row is None:
            return error.error_authorization_fail()

        if password != row[0]:
            return error.error_authorization_fail()

        return 200, "ok"
    #定义登录函数
    #得到用户的id，密码，终端之后，检查用户的密码输入是否正确，重新生成令牌并在usr中更新
    def login(self, user_id: str, password: str, terminal: str) -> (int, str, str):
        token = ""
        try:
            code, message = self.check_password(user_id, password)
            if code != 200:
                return code, message, ""

            token = jwt_encode(user_id, terminal)
            self.cursor = self.conn.cursor()
            self.cursor.execute(
                "UPDATE usr set token= '%s' , terminal = '%s' where user_id = '%s'"
               % (token, terminal, user_id) )
            #print(self.cursor.rowcount)
            if self.cursor.rowcount == 0: ##
                return error.error_authorization_fail() + ("", )
            self.conn.commit()
        except psycopg2.errors.UniqueViolation:
            return error.error_exist_user_id(user_id)
        return 200, "ok", token
    #定义logout函数，登出函数
    #检查用户令牌，然后生成新的用户令牌并在usr中更新
    def logout(self, user_id: str, token: str) -> bool:
        try:
            code, message = self.check_token(user_id, token)
            if code != 200:
                return code, message

            terminal = "terminal_{}".format(str(time.time()))
            dummy_token = jwt_encode(user_id, terminal)
            self.cursor = self.conn.cursor()
            self.cursor.execute(
                "UPDATE usr SET token = '%s', terminal = '%s' WHERE user_id='%s'" %
                (dummy_token, terminal, user_id) )
            if self.cursor.rowcount == 0:
                return error.error_authorization_fail()

            self.conn.commit()
        except psycopg2.errors.UniqueViolation:
            return error.error_exist_user_id(user_id)
        return 200, "ok"
    #定义注销函数
    #检查用户输入的密码是否正确，然后在usr中删除用户信息
    def unregister(self, user_id: str, password: str) -> (int, str):
        try:
            code, message = self.check_password(user_id, password)
            if code != 200:
                return code, message
            self.cursor = self.conn.cursor()
            self.cursor.execute("DELETE from usr where user_id='%s'" % (user_id))
            #print(self.cursor.rowcount)
            if self.cursor.rowcount == 1:
                self.conn.commit()
            else:
                return error.error_authorization_fail()
        except psycopg2.errors.UniqueViolation:
            return error.error_exist_user_id(user_id)
        return 200, "ok"
    #定义更改密码函数
    #检查用户输入的密码，生成新的令牌，获取新的密码，并在usr中更新
    def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        try:
            code, message = self.check_password(user_id, old_password)
            if code != 200:
                return code, message

            terminal = "terminal_{}".format(str(time.time()))
            token = jwt_encode(user_id, terminal)
            self.cursor = self.conn.cursor()
            self.cursor.execute(
                "UPDATE usr set password = '%s', token= '%s' , terminal = '%s' where user_id = '%s'" %
                (new_password, token, terminal, user_id), )
            if self.cursor.rowcount == 0:
                return error.error_authorization_fail()

            self.conn.commit()
        except psycopg2.errors.UniqueViolation:
            return error.error_exist_user_id(user_id)
        return 200, "ok"

