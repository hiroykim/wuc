#!/usr/bin/python
# -*- coding:utf-8 -*-

"""program"""
__author__ = "MINDsLAB"
__date__ = "creation: 2020-11-12, modification: 0000-00-00"

###########
# imports #
###########
import subprocess

missing_list = list()
required_list = [
    'import zmq',
    'import lxml',
    'import grpc',
    'import numpy',
    'import flask',
    'import Crypto',
    'import socket',
    'import gensim',
    'import theano',
    'import pymssql',
    'import pymysql',
    'import tornado',
    'import gunicorn',
    'import requests',
    'import cx_Oracle',
    'import flask_cors',
    'import virtualenv',
    'import flask_restful',
    'import elasticsearch',
    'import google.protobuf',
    'import apscheduler.schedulers.background'
]
for item in required_list:
    cmd = "python -c '{0}'".format(item)
    sub_pro = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    response_out, response_err = sub_pro.communicate()
    if response_err.strip():
        missing_list.append(item)
if missing_list:
    print("Can't import list")
    for item in missing_list:
        print('  --> {0}'.format(item))
else:
    print("Import success")

