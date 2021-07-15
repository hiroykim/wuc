#! /usr/bin/env python
#-*- coding: utf-8 -*-

import sys
from importlib import reload

reload(sys)

import os
import requests
import json
import traceback

from pprint import pprint
import logging.handlers
from voice_bot.ai_da_lib import logger
from voice_bot.config.config import DaConfig
from voice_bot.config.config import SimpleBotMaumSDSConfig


# exe_path = os.path.realpath(sys.argv[0])
# bin_path = os.path.dirname(exe_path)
# lib_path = os.path.realpath(bin_path + '/../lib/python')
sys.path.append(os.path.join(os.getenv('MAUM_ROOT'), 'lib/python'))
# sys.path.append(os.path.realpath(sys.argv[0] + '/..'))
# sys.path.append(lib_path)


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
    srv_address = ''
    url = ''
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
        self.logger.debug('[maum-sds] __init__')
        self.srv_address = MaumSdsConfig.srv_address
        self.url = MaumSdsConfig.url
        self.host = MaumSdsConfig.host
        self.lang = MaumSdsConfig.lang
        self.header1 = MaumSdsConfig.header1
        self.header2 = MaumSdsConfig.header2
        self.session = 'session_from_da_test'
        self.entity_list = []

        self.logger.debug('[maum-sds] srv_address : {}'.format(self.srv_address))
        self.logger.debug('[maum-sds] url : {}'.format(self.url))
        # self.logger.debug('[maum-sds] host : {}'.format(self.host))
        # self.logger.debug('[maum-sds] lang : {}'.format(self.lang))

    def get_collector_uri(self, type=TYPE_UTTER):
        if type == self.TYPE_UTTER:
            srv_uri = 'http://' + self.srv_address + '/' + self.url
        else:
            srv_uri = 'http://' + self.srv_address + '/collect/run/intent'
        return srv_uri

    def call_maum_sds(self, utter='', session='', type=TYPE_UTTER, entities=[]):
        # results
        answer = ''
        intent = ''
        res_content = dict()
        try:

            # requests
            srv_uri = self.get_collector_uri(type)

            headers = {
                'Content-Type': 'application/json',
                'cache-control': 'no-cache',
            }
            if not session:
                session = self.session
            data_param = {'host': self.host, 'session': session, 'data': {type: utter},
                          'lang': self.lang, 'entities': entities}
            response = requests.post(srv_uri, headers=headers, data=json.dumps(data_param))

            self.logger.debug('[maum-sds] srv_uri : {}'.format(srv_uri))
            self.logger.debug('[maum-sds] host: {}'.format(self.host))
            self.logger.debug('[maum-sds] session: {}'.format(session))

            self.logger.debug('[maum-sds] data: {}'.format({type: utter}))
            self.logger.debug('[maum-sds] entities: {}'.format(entities))

            self.logger.debug('[maum-sds] response.text : ')
            pprint(json.loads(response.text))

            if response.ok:
                # res_content = json.loads(response.content, object_hook=_byteify) #갑자기 안먹힘
                # res_content = json.loads(response.content, object_hook=None) #챗봇에선 먹히고 음성봇에선 안먹힘
                res_content = json.loads(response.text)
                # self.logger.debug('[maum-sds] res_content : {}'.format(res_content))
                if 'answer' in res_content:
                    if 'answer' in res_content['answer']:
                        answer = res_content['answer']['answer']
                if 'setMemory' in res_content:
                    if 'intent' in res_content['setMemory']:
                        intent = res_content['setMemory']['intent']['intent']
            else:
                self.logger.error('[maum-sds] talk failed , response: {}'.format(response.text))

            #if answer is None or answer == '': raise Exception('SDS answer empty!')
        except Exception:
            self.logger.error('[maum-sds] talk fail!, err:')
            traceback.print_exc()
            answer = '죄송합니다. 내부 문제로 답변할 수 없습니다!'

        self.logger.debug('[maum-sds] Intent : {}'.format(intent))
        self.logger.debug('[maum-sds] Answer : {}'.format(answer))
        return answer, intent, res_content

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
        self.logger.debug('[maum-sds] answer: ' + answer + '/' + intent)
        return answer, intent

if __name__ == '__main__':
    log = logger.get_timed_rotating_logger(
        logger_name=DaConfig.logger_name,
        log_dir_path=DaConfig.log_dir_path,
        log_file_name=DaConfig.log_file_name,
        backup_count=DaConfig.log_backup_count,
        log_level=DaConfig.log_level
    )
    log.setLevel(logging.DEBUG)
    sds = MaumSds(SimpleBotMaumSDSConfig, log)
    sds.call_maum_sds('처음으로', sds.session)

