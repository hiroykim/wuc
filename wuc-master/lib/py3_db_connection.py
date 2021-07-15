#!/usr/bin/python
# -*- coding:utf-8 -*-

"""program"""
__author__ = "MINDsLAB"
__date__ = "creation: 2021-02-08, modification: 0000-00-00"

###########
# imports #
###########
import os
import time
import cx_Oracle
import traceback


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


if __name__ == '__main__':
    class OracleConfig(object):
        host = '127.0.0.1'
        host_list = ['127.0.0.1', ]
        user = 'user'
        pd = 'password'
        port = 3521
        sid = 'TEST'
        service_name = 'TEST'
        reconnect_interval = 10

    db = Oracle(OracleConfig, failover=True, service_name=True)
    # query = """
    # """
    # db.cursor.execute(query,)
    # result = db.cursor.fetchall()
    # for item in result:
    #     print item
    # db.conn.commit()
    db.disconnect()
