#!/usr/bin/python
# -*- coding:utf-8 -*-

"""program"""
__author__ = "MINDsLAB"
__date__ = "creation: 2020-12-08, modification: 0000-00-00"

###########
# imports #
###########
import sys
import json
import socket
import requests

###########
# options #
###########
reload(sys)
sys.setdefaultencoding("utf-8")

if __name__ == '__main__':
    port = 8787
    ##
#    host = 'http://10.20.20.65:{1}/check_pro'.format(socket.gethostbyname(socket.gethostname()), port)
#    print("\n*  Check API [{0}]  *".format(host))
#    payload = {'pro_name': 'brain'}
#    result = requests.post(host, data=payload)
#    pro_cnt = json.loads(result.text)
#    print(pro_cnt)
    ##
    host = "http://10.20.20.65:{1}/check_svctl".format(socket.gethostbyname(socket.gethostname()), port)
    print("\n*  Check API [{0}]  *".format(host))
#    req_result = requests.post(host)
#    response_out = json.loads(req_result.text)
#    print(response_out)
    ##
    host = "http://10.20.20.65:{1}/call_rsvt_cncl".format(socket.gethostbyname(socket.gethostname()), port)
    print("\n*  Check API [{0}]  *".format(host))
    payload = {
        'cust_tel_no': '01092444745',
        'call_time': '202107071150'
    }
    req_result = requests.post(host, json=payload)
    response_out = json.loads(req_result.text)
    print(response_out)
    ##
#    host = "http://10.20.20.65:{1}/nlp".format(socket.gethostbyname(socket.gethostname()), port)
#    print("\n*  Check API [{0}]  *".format(host))
#    target_str = '안녕하세요 테스트 문장입니다'
#    payload = {
#        'uni_id': '1',
#        'target_str': target_str,
#        'engn': 'nlp3'
#    }
#    result = requests.post(host, json=payload)
#    if result:
#        result_dict = json.loads(result.text)
#        for key, value in result_dict.items():
#            print(key, ':', value)
#    else:
#        print('Error', result)
#    ##
#    host = "http://10.20.20.65:{1}/hmd".format(socket.gethostbyname(socket.gethostname()), port)
#    print("\n*  Check API [{0}]  *".format(host))
#    target_str = """
#    안녕하세요 고객님
#    상담원 홍길동입니다
#    녹음을 시작하겠습니다
#        """
#    payload = {
#        'uni_id': '1',
#        'target_str': target_str,
#        'hmd_info': [
#            {'cate': 'test1', 'rule': '(안녕)'},
#            {'cate': 'test2', 'rule': '(상담원)'}
#        ]
#    }
#    result = requests.post(host, json=payload)
#    if result:
#        result_dict = json.loads(result.text)
#        print('result_dict: {0}'.format(result_dict))
#        for key, value in result_dict.items():
#            print(key, ':', value)
#    else:
#        print('Error', result)
