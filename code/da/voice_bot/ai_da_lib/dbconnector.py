#-*- coding: utf-8 -*-
import pymysql

class DbConnector:
    ai_host = ''
    ai_user = ''
    ai_pw = ''
    ai_database = ''
    charset = ''
    def __init__(self, Config):
        self.ai_host = Config.host
        self.ai_user = Config.user
        self.ai_pw = Config.passwd
        self.ai_database = Config.db
        self.charset = 'utf8'

    def get_connection(self):
        return pymysql.connect(self.ai_host, self.ai_user, self.ai_pw, self.ai_database, charset=self.charset)
    """
    function: execute_with_param
    sql: string 쿼리
    params: string 파라미터
    """
    def execute_with_param(self, sql, param):
        conn = self.get_connection()
        row = None
        try:
            print('[sql]:', sql)
            print('[param]:', param)
            curs = conn.cursor()
            curs.execute(sql, [param])
            row = curs.fetchone()
        except Exception as e:
            print('[db error]: ', e)
        finally:
            conn.close()
            return row

    def select_one(self, sql):
        conn = self.get_connection()
        row = None
        try:
            print('[sql]:', sql)
            curs = conn.cursor()
            curs.execute(sql)
            row = curs.fetchone()
        except Exception as e:
            print('[db error]: ', e)
        finally:
            conn.close()
        return row

    def select_one_dict(self, sql):
        conn = self.get_connection()
        row = None
        try:
            print('[sql]:', sql)
            curs = conn.cursor(pymysql.cursors.DictCursor)
            curs.execute(sql)
            row = curs.fetchone()
        except Exception as e:
            print('[db error]: ', e)
        finally:
            conn.close()
            return row

    def select_all(self, sql):
        conn = self.get_connection()
        row = None
        try:
            print('[sql]:', sql)
            curs = conn.cursor()
            curs.execute(sql)
            row = curs.fetchall()
        except Exception as e:
            print('[db error]: ', e)
        finally:
            conn.close()
            return row


    def execute_without_param(self, sql):
        conn = self.get_connection()
        row = None
        try:
            curs = conn.cursor()
            curs.execute(sql)
            row = curs.fetchone()
        except Exception as e:
            print('[db error]: ', e)
        finally:
            conn.close()
            return row
    def execute_without_param_all(self, sql):
        conn = self.get_connection()
        row = None
        try:
            curs = conn.cursor()
            curs.execute(sql)
            row = curs.fetchall()
        except Exception as e:
            print('[db error]: ', e)
        finally:
            conn.close()
            return row


    """
    function: execute_with_params(
    sql: string 쿼리
    params: tuple 파라미터
    """
    def execute_with_params(self, sql, params):
        conn = self.get_connection()
        row = None
        try:
            # todo check (params)
            curs = conn.cursor()
            curs.execute(sql, params)
            row = curs.fetchone()
        except Exception as e:
            print('[db error]: ', e)
        finally:
            conn.close()
            return row
    """
    function: insertexecute_with_params(
    sql: string 쿼리
    params: tuple 파라미터
    """
    def insertexecute_with_params(self, sql, params):
        conn = self.get_connection()
        try:
            # todo check (params)
            curs = conn.cursor()
            curs.execute(sql, params)
            conn.commit()
        except Exception as e:
            print('[db error]: ', e)
        finally:
            conn.close()

    """
    function: execute_query_with_params
    sql: string 쿼리
    params: tuple 파라미터
    """
    def execute_query_with_params(self, sql, params):
        res = -1
        conn = self.get_connection()
        try:
            # todo check (params)
            curs = conn.cursor()
            curs.execute(sql, params)
            conn.commit()
            res = curs.lastrowid
        except Exception as e:
            print('[db error]: ', e)
        finally:
            conn.close()
            return res

    """
    function: update_query_with_params
    sql: string 쿼리
    params: tuple 파라미터
    """
    def update_query_with_params(self, sql, params):
        res = -1
        conn = self.get_connection()
        try:
            curs = conn.cursor()
            curs.execute(sql, params)
            conn.commit()
            res = curs.rowcount
        except Exception as e:
            print('[db error]: ', e)
        finally:
            conn.close()
            return res

if __name__ == "__main__":
    a = 'dbconn'
