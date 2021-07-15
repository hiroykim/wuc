#!/usr/bin/python
# -*- coding:utf-8 -*-

"""program"""
__author__ = "MINDsLAB"
__date__ = "creation: 2018-08-24, modification: 0000-00-00"

###########
# imports #
###########
import os
import sys
import time
import pymssql
import pymysql
import cx_Oracle
import traceback
import subprocess

###########
# options #
###########
reload(sys)
sys.setdefaultencoding("utf-8")


#########
# class #
#########
class Oracle(object):
    def __init__(self, conf, host_reverse=False, failover=False, service_name=False):
        self.conf = conf
        os.environ["NLS_LANG"] = ".AL32UTF8"
        if failover:
            self.dsn_tns = '(DESCRIPTION = (ADDRESS_LIST= (FAILOVER = on)(LOAD_BALANCE = off)'
            if host_reverse:
                self.conf.host_list.reverse()
            for host in self.conf.host_list:
                self.dsn_tns += '(ADDRESS= (PROTOCOL = TCP)(HOST = {0})(PORT = {1}))'.format(host, self.conf.port)
            if service_name:
                self.dsn_tns += ')(CONNECT_DATA=(SERVICE_NAME={0})))'.format(self.conf.service_name)
            else:
                self.dsn_tns += ')(CONNECT_DATA=(SID={0})))'.format(self.conf.sid)
        else:
            if service_name:
                self.dsn_tns = cx_Oracle.makedsn(
                    self.conf.host,
                    self.conf.port,
                    service_name=self.conf.service_name
                )
            else:
                self.dsn_tns = cx_Oracle.makedsn(
                    self.conf.host,
                    self.conf.port,
                    sid=self.conf.sid
                )
        self.conn = cx_Oracle.connect(
            self.conf.user,
            self.conf.pd,
            self.dsn_tns
        )
        self.cursor = self.conn.cursor()

    def disconnect(self):
        try:
            self.cursor.close()
            self.conn.close()
        except Exception:
            raise Exception(traceback.format_exc())

    def check_alive(self):
        try:
            self.cursor.execute("SELECT 'TEST' FROM DUAL")
        except cx_Oracle.DatabaseError as e:
            error, = e.args
            if error.code == 1033:
                time.sleep(self.conf.reconnect_interval)
                self.__init__(self.conf, host_reverse=True, failover=True, service_name=False)
            else:
                self.__init__(self.conf)


class MSSQL(object):
    def __init__(self, conf):
        self.conf = conf
        self.conn = pymssql.connect(
            host=self.conf.host,
            user=self.conf.user,
            # password=self.openssl_dec(),
            password=self.conf.pd,
            database=self.conf.database,
            port=self.conf.port,
            charset=self.conf.charset,
            login_timeout=self.conf.login_timeout
        )
        self.conn.autocommit(False)
        self.cursor = self.conn.cursor()

    def disconnect(self):
        try:
            self.cursor.close()
            self.conn.close()
        except Exception:
            raise Exception(traceback.format_exc())

    def check_alive(self):
        try:
            self.cursor.execute("SELECT 'TEST'")
        except pymssql.DatabaseError:
            time.sleep(self.conf.reconnect_interval)
            self.__init__(self.conf)

    @staticmethod
    def sub_process(cmd):
        sub_pro = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        response_out, response_err = sub_pro.communicate()
        return response_out, response_err

    def openssl_dec(self):
        cmd = "openssl enc -seed -d -a -in {0} -pass file:{1}".format(self.conf.pd, self.conf.ps_path)
        std_out, std_err = self.sub_process(cmd)
        return std_out.strip()


class MYSQL(object):
    def __init__(self, conf):
        self.conf = conf
        self.conn = pymysql.connect(
            host=self.conf.host,
            user=self.conf.user,
            # password=self.openssl_dec(),
            passwd=self.conf.pd,
            db=self.conf.database,
            port=self.conf.port,
            charset=self.conf.charset
        )
        self.conn.autocommit(False)
        self.cursor = self.conn.cursor()

    def disconnect(self):
        try:
            self.cursor.close()
            self.conn.close()
        except Exception:
            raise Exception(traceback.format_exc())

    def check_alive(self):
        try:
            self.cursor.execute("SELECT 'TEST'")
        except pymysql.DatabaseError:
            time.sleep(self.conf.reconnect_interval)
            self.__init__(self.conf)

    @staticmethod
    def sub_process(cmd):
        sub_pro = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        response_out, response_err = sub_pro.communicate()
        return response_out, response_err

    def openssl_dec(self):
        cmd = "openssl enc -seed -d -a -in {0} -pass file:{1}".format(self.conf.pd, self.conf.ps_path)
        std_out, std_err = self.sub_process(cmd)
        return std_out.strip()


if __name__ == '__main__':
    class MYConfig(object):
        host = '127.0.0.1'
        user = 'user'
        pd = 'password'
        port = 1433
        charset = 'utf8'
        database = 'TEST'
        login_timeout = 10

    db = MSSQL(MYConfig)
    # query = """
    # """
    # db.cursor.execute(query,)
    # result = db.cursor.fetchall()
    # for item in result:
    #     print item
    # db.conn.commit()
    db.disconnect()
