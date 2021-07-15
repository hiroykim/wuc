#! /usr/bin/env python
#-*- coding: utf-8 -*-

import sys
from importlib import reload

reload(sys)

import os
import requests
import json
import traceback

exe_path = os.path.realpath(sys.argv[0])
bin_path = os.path.dirname(exe_path)
lib_path = os.path.realpath(bin_path + '/../lib/python')
sys.path.append(os.path.join(os.getenv('MAUM_ROOT'), 'lib/python'))
sys.path.append(os.path.realpath(sys.argv[0] + '/..'))
sys.path.append(lib_path)


def _byteify(data, ignore_dicts = False):
    if isinstance(data, unicode):
        return data.encode('utf-8')
    if isinstance(data, list):
        return [ _byteify(item, ignore_dicts=True) for item in data ]
    if isinstance(data, dict) and not ignore_dicts:
        return {
            _byteify(key, ignore_dicts=True): _byteify(value, ignore_dicts=True)
            for key, value in data.iteritems()
        }
    return data


class MaumSds:
    svc_host = ''
    svc_path = ''
    host = ''
    lang = ''
    header1 = ''
    header2 = ''
    logger = None
    session = None
    TYPE_INTENT = 'intent'
    TYPE_UTTER = 'utter'

    def __init__(self, MaumSdsConfig, logger = None):
        self.logger = logger
        self.logger.debug('[sds]init end')
        self.srv_address = MaumSdsConfig.srv_address
        self.host = MaumSdsConfig.host
        self.url = MaumSdsConfig.url
        self.lang = MaumSdsConfig.lang
        self.header1 = MaumSdsConfig.header1
        self.header2 = MaumSdsConfig.header2
        self.session = 'test'

    def get_collector_url(self, type=TYPE_UTTER):
        if type == self.TYPE_UTTER:
            srv_url = 'http://' + self.srv_address + '/' + self.url
        else:
            srv_url = 'http://' + self.srv_address + '/collect/run/intent'
        return srv_url

    def call_maum_sds(self, utter='', session='', type=TYPE_UTTER, entities=[]):
        answer = ''
        intent = ''
        res_content = dict()
        try:
            srv_url = self.get_collector_url(type)
            headers = {
                'Content-Type': 'application/json',
                'cache-control': 'no-cache',
            }
            if not session:
                session = self.session
            data_param = {'host': self.host, 'session': session, 'data': {type: utter}, 'lang': self.lang, 'entities': entities}
            self.logger.info(srv_url)
            self.logger.info(headers)
            self.logger.info(data_param)

            response = requests.post(srv_url, headers=headers, data=json.dumps(data_param))

            self.logger.debug('request url: {}'.format(srv_url))
            self.logger.debug('request: {}'.format(data_param))
            self.logger.debug('response : {}'.format(response))
            self.logger.debug('response.text : {}'.format(response.text))

            if response.ok:
                res_content = json.loads(response.text)
                if 'answer' in res_content:
                    if 'answer' in res_content['answer']:
                        answer = res_content['answer']['answer']
                if 'setMemory' in res_content:
                    if 'intent' in res_content['setMemory']:
                        intent = res_content['setMemory']['intent']['intent']
            else:
                self.logger.error('[maum-sds] talk failed, response: {}'.format(response.text))

        except Exception:
            self.logger.error('[maum-sds] talk failed, err:')
            traceback.print_exc()
            answer = '죄송합니다. 내부 문제로 답변할 수 없습니다.!'

        self.logger.debug('[Call Maum Sds] answer: ' + answer + '/' + intent)
        return answer, intent, res_content

    def CallMaumSds(self, text='', session='', type=TYPE_UTTER, entities=[]):
        answer = ''
        intent = ''
        headers = {
            'Content-Type': 'application/json',
            'cache-control': 'no-cache',
        }
        url = 'http://' + self.host + '/' + self.url
        data_param = {'host': self.host, 'session': session, 'data': {'utter': text}, 'lang': self.lang}
        self.logger.debug('request url: {}'.format(url))
        self.logger.debug('request: {}'.format(data_param))
        response = requests.post(url, headers=headers, data=json.dumps(data_param))
        self.logger.debug('response : {}'.format(response))
        self.logger.debug('response.text : {}'.format(response.text))
        if response.ok:
            cont = response.content
            cv_res_js = json.loads(cont, object_hook=_byteify)
            # print cv_res_js
            # print cv_res_js['answer']['answer']
            self.logger.debug('cv_res_js : {}'.format(cv_res_js))
            if 'answer' in cv_res_js:
                # print '===='
                if 'answer' in cv_res_js['answer']:
                    answer = cv_res_js['answer']['answer']
            if 'setMemory' in cv_res_js:
                if 'intent' in cv_res_js['setMemory']:
                    intent = cv_res_js['setMemory']['intent']['intent']
        self.logger.debug('[Call Maum Sds] answer: ' + answer + '/' + intent)
        return answer, intent

    def CallSimpleMaumSds(self, url='', host='', text='', session='', lang='1'):
        answer = ''
        intent = ''
        headers = {
            'Content-Type': 'application/json',
            'cache-control': 'no-cache',
        }
        data_param = {'host': host, 'session': session, 'data': {'utter': text}, 'lang': lang}
        if text == '처음으로':
            url = url.replace('/run/utter', '/run/intent')
            data_param['data'] = {"intent": "처음으로"}
        response = requests.post(url, headers=headers, data=json.dumps(data_param))
        if response.ok:
            cont = response.content
            cv_res_js = json.loads(cont, object_hook=_byteify)
            if 'answer' in cv_res_js:
                if 'answer' in cv_res_js['answer']:
                    answer = cv_res_js['answer']['answer']
            if 'setMemory' in cv_res_js:
                if 'intent' in cv_res_js['setMemory']:
                    intent = cv_res_js['setMemory']['intent']['intent']
        self.logger.debug('[Call Maum Sds] answer: ' + answer + '/' + intent)
        return answer, intent

if __name__ == '__main__':
    sds = MaumSds()
    sds.CallMaumSds('테스트합니다.')
    # print exe_path, os.path.realpath(sys.argv[0] + '/../../')
