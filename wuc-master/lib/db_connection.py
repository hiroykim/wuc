#!/usr/bin/python
# -*- coding: utf-8 -*-

"""program"""
__author__ = "MINDsLAB"
__date__ = "creation: 2020-09-07, modification: 0000-00-00"

###########
# imports #
###########
import os
import time
import pymysql
import traceback
import subprocess


#########
# class #
#########
class MYSQL(object):
    def __init__(self, conf):
        self.conf = conf
        self.conn = pymysql.connect(
            host=self.conf.host,
            user=self.conf.user,
            passwd=self.openssl_dec(),
            db=self.conf.database,
            port=self.conf.port,
            charset=self.conf.charset,
            connect_timeout=self.conf.connect_timeout,
            autocommit=True,
        )
        self.conn.autocommit(True)
        self.cursor = self.conn.cursor(pymysql.cursors.DictCursor)

    @staticmethod
    def sub_process(cmd):
        sub_pro = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        response_out, response_err = sub_pro.communicate()
        return response_out, response_err

    def openssl_dec(self):
        cmd = "openssl enc -seed -d -a -in {0} -pass file:{1}".format(self.conf.pd, self.conf.ps_path)
        print('cmd: {0}'.format(cmd))
        std_out, std_err = self.sub_process(cmd)
        return std_out.strip()

    def disconnect(self):
        try:
            self.cursor.close()
            self.conn.close()
        except Exception:
            raise Exception(traceback.format_exc())

    def check_alive(self):
        try:
            self.cursor.execute("SELECT 'TEST' FROM DUAL")
        except pymysql.DatabaseError as e:
            time.sleep(self.conf.reconnect_interval)
            self.__init__(self.conf)
        except pymysql.InterfaceError as e:
            time.sleep(self.conf.reconnect_interval)
            self.__init__(self.conf)
        except Exception:
            time.sleep(self.conf.reconnect_interval)
            self.__init__(self.conf)


class MSSQL(object):
    def __init__(self, conf):
        self.conf = conf
        import pymssql
        self.conn = pymssql.connect(
            host=self.conf.host,
            user=self.conf.user,
            password=self.openssl_dec(),
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
        import pymssql
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


########
# main #
########
def rows_to_dict_list(db):
    """
    Make dict Result
    @param         db:         DB object
    @return:                   Dictionary Result
    """
    columns = [i[0] for i in db.cursor.description]
    return [dict(zip(columns, row)) for row in db.cursor]


if __name__ == '__main__':
    class MYConfig(object):
        host = '10.219.2.97'
        host_list = ['10.219.2.97']
        user = 'minds'    # mindslab1!
        pd = '/stt_nas/Stt_Real/cfg/.mystt'
        ps_path = '/stt_nas/Stt_Real/cfg/.fubonhyundai'
        port = 3306
        charset = 'utf8'
        database = 'MAUMQA'
        connect_timeout = 5
        reconnect_interval = 20

    class CSORAConfig(object):
        # host = '10.219.6.18'
        host_list = ['10.219.2.3', '10.219.2.2']
        user = 'STT'
        pd = '/stt_nas/Stt_Real/cfg/.csorastt'
        ps_path = '/stt_nas/Stt_Real/cfg/.fubonhyundai'
        port = 1571
        service_name = 'HDLI01'
        sid = 'HDLI01'
        reconnect_interval = 10

    class TMORAConfig(object):
        # host = '10.219.2.103'
        host_list = ['10.219.2.103', '10.219.2.102']
        user = 'STT'
        pd = '/stt_nas/Stt_Real/cfg/.tmorastt'
        ps_path = '/stt_nas/Stt_Real/cfg/.fubonhyundai'
        port = 1584
        service_name = 'HDLI14'
        sid = 'HDLI14D'
        reconnect_interval = 10
    import sys
    sys.path.append('/appl/maum')
    from cfg import config
    mysql = MYSQL(config.MYConfig)
    from lib import util
    results = util.select_contract_no(mysql, '202107071150', '901092444745')
    print(results)
    query = """
SELECT
                B.CONTRACT_NO
            FROM
                CUST_INFO A,
                CM_CONTRACT B
            WHERE
                A.CUST_TEL_NO = '901092444745'
                AND JSON_UNQUOTE(JSON_EXTRACT(A.CUST_DATA, '$."8"')) LIKE '%{0}%'
                AND A.CUST_ID = B.CUST_ID
    """.format('202107071150')
    mysql.cursor.execute(query,)
    result = mysql.cursor.fetchall()
    for item in result:
        print(item)
    mysql.conn.commit()
    mysql.disconnect()
