#!/usr/bin/python
# -*- coding: utf-8 -*-

"""program"""
__author__ = "MINDsLAB"
__date__ = "creation: 2020-12-08, modification: 0000-00-00"

###########
# imports #
###########
import os
import sys
import grpc
import time
import traceback
import subprocess
from datetime import datetime
from flask import Flask, request
from flask_cors import CORS
from google.protobuf import json_format
from flask_restful import reqparse, Api, Resource
sys.path.append(os.path.join(os.getenv('MAUM_ROOT'), 'lib/python'))
from common.config import Config
from maum.common import lang_pb2
from maum.brain.nlp import nlp_pb2, nlp_pb2_grpc
from maum.brain.hmd import hmd_pb2, hmd_pb2_grpc
sys.path.append('/appl/maum')
from cfg import config
from lib import util, db_connection

###########
# options #
###########
reload(sys)
sys.setdefaultencoding("utf-8")


#########
# class #
#########
class CheckProAPI(Resource):
    def __init__(self):
        self.pro_name = request.form.get('pro_name')

    def post(self):
        return check_process(self.pro_name)


class CheckSupervisorAPI(Resource):
    @staticmethod
    def post():
        return check_supervisor()


class CallReservationCancel(Resource):
    def __init__(self):
        self.json_data = request.get_json(silent=True, cache=False, force=True)
        print(self.json_data)
        self.cust_tel_no = self.json_data.get('cust_tel_no')
        self.call_time = self.json_data.get('call_time')
        self.mysql_db = self.connect_db('MYSQL', config.MYConfig)

    def post(self):
        return cancel_reservation(self.mysql_db, self.cust_tel_no, self.call_time)

    def connect_db(self, db_type, db_conf):
        db = ''
        flag = True
        while flag:
            try:
                print('Try connecting to {0} DB ...'.format(db_type))
                if db_type.upper() == 'MSSQL':
                    db = db_connection.MSSQL(db_conf)
                    flag = False
                elif db_type.upper() == 'MYSQL':
                    db = db_connection.MYSQL(db_conf)
                    flag = False
                else:
                    raise Exception('Not supported db ..(Oracle, MSSQL, MYSQL)')
                print('Success connect to {0} DB'.format(db_type))
            except Exception:
                err_str = traceback.format_exc()
                print(err_str)
                time.sleep(60)
        return db


class NlpClient(object):
    def __init__(self, engine):
        self.conf = Config()
        self.conf.init('brain-ta.conf')
        if engine.lower() == 'nlp1':
            self.remote = 'localhost:{0}'.format(self.conf.get('brain-ta.nlp.1.kor.port'))
            channel = grpc.insecure_channel(self.remote)
            self.stub = nlp_pb2_grpc.NaturalLanguageProcessingServiceStub(channel)
        elif engine.lower() == 'nlp2':
            self.remote = 'localhost:{0}'.format(self.conf.get('brain-ta.nlp.2.kor.port'))
            channel = grpc.insecure_channel(self.remote)
            self.stub = nlp_pb2_grpc.NaturalLanguageProcessingServiceStub(channel)
        elif engine.lower() == 'nlp3':
            self.remote = 'localhost:{0}'.format(self.conf.get('brain-ta.nlp.3.kor.port'))
            channel = grpc.insecure_channel(self.remote)
            self.stub = nlp_pb2_grpc.NaturalLanguageProcessingServiceStub(channel)
        else:
            print('Not existed Engine')
            raise Exception('Not existed Engine')

    def analyze(self, target_text):
        in_text = nlp_pb2.InputText()
        try:
            in_text.text = target_text.replace('*', ' ')
        except Exception:
            in_text.text = unicode(target_text.replace('*', ' '), 'euc-kr').encode('utf-8')
            target_text = unicode(target_text, 'euc-kr').encode('utf-8')
        in_text.lang = lang_pb2.kor
        in_text.split_sentence = True
        in_text.use_tokenizer = False
        in_text.use_space = False
        in_text.level = 1
        in_text.keyword_frequency_level = 0
        ret = self.stub.Analyze(in_text)
        tmp_nlp_list = list()
        tmp_morph_list = list()
        for idx in range(len(ret.sentences)):
            nlp_word_list = list()
            morph_word_list = list()
            analysis = ret.sentences[idx].morps
            for ana_idx in range(len(analysis)):
                morphs_word = analysis[ana_idx].lemma.encode('utf-8')
                morphs_type = analysis[ana_idx].type.split('[')[0].strip()
                if morphs_type in ['VV', 'VA', 'VX', 'VCP', 'VCN']:
                    nlp_word_list.append('{0}다'.format(morphs_word))
                    morph_word_list.append('{0}다/{1}'.format(morphs_word, morphs_type))
                else:
                    nlp_word_list.append('{0}'.format(morphs_word))
                    morph_word_list.append('{0}/{1}'.format(morphs_word, morphs_type))
            tmp_nlp_list.append(' '.join(nlp_word_list))
            tmp_morph_list.append(' '.join(morph_word_list))
        result = (target_text, ' '.join(tmp_nlp_list).strip(), ' '.join(tmp_morph_list).strip())
        return result


class HmdClient(object):
    def __init__(self):
        self.conf = Config()
        self.conf.init('brain-ta.conf')
        remote = 'localhost:{0}'.format(self.conf.get('brain-ta.hmd.front.port'))
        channel = grpc.insecure_channel(remote)
        self.stub = hmd_pb2_grpc.HmdClassifierStub(channel)

    def set_model(self, model_name, hmd_model_list):
        model = hmd_pb2.HmdModel()
        model.lang = lang_pb2.kor
        model.model = model_name
        rules_list = list()
        for item in hmd_model_list:
            hmd_client = hmd_pb2.HmdRule()
            hmd_client.rule = item[1]
            hmd_client.categories.extend(item[0])
            rules_list.append(hmd_client)
        model.rules.extend(rules_list)
        self.stub.set_model(model)

    def get_class_by_text(self, model_name, text, nlp_vs='nlp3'):
        in_doc = hmd_pb2.HmdInputText()
        in_doc.text = text
        in_doc.model = model_name
        in_doc.lang = lang_pb2.kor
        in_doc.nlp_vs = nlp_vs
        ret = self.stub.get_class_by_text(in_doc)
        json_ret = json_format.MessageToJson(ret, True)
        return json_ret

    def load_model(self, model_name):
        model_path = '{0}/{1}__0.hmdmodel'.format(self.conf.get('brain-ta.hmd.model.dir'), model_name)
        in_file = open(model_path, 'rb')
        hm = hmd_pb2.HmdModel()
        hm.ParseFromString(in_file.read())
        in_file.close()
        return hm

    @staticmethod
    def split_hmd_rule(rule):
        flag = False
        detect_rule = str()
        rule_list = list()
        for idx in range(len(rule)):
            if rule[idx] == '(':
                flag = True
            elif rule[idx] == ')' and len(detect_rule) != 0:
                rule_list.append(detect_rule)
                detect_rule = str()
                flag = False
            elif flag:
                detect_rule += rule[idx]
        return rule_list

    def vec_word_combine(self, tmp_list, category, dtc_keyword, dtc_keyword_list, level, hmd_rule):
        if level == len(dtc_keyword_list):
            tmp_list.append((category, dtc_keyword, hmd_rule))
        elif level == 0:
            for idx in range(len(dtc_keyword_list[level])):
                tmp_dtc_keyword = dtc_keyword_list[level][idx]
                self.vec_word_combine(tmp_list, category, tmp_dtc_keyword, dtc_keyword_list, level + 1, hmd_rule)
        else:
            for idx in range(len(dtc_keyword_list[level])):
                if dtc_keyword[-1] == '@':
                    tmp_dtc_keyword = dtc_keyword[:-1] + '$@' + dtc_keyword_list[level][idx]
                elif dtc_keyword[-1] == '%':
                    tmp_dtc_keyword = dtc_keyword[:-1] + '$%' + dtc_keyword_list[level][idx]
                elif len(dtc_keyword) > 1 and dtc_keyword[-2] == '+' and ('0' <= dtc_keyword[-1] <= '9'):
                    tmp_dtc_keyword = dtc_keyword[:-1] + '$+' + dtc_keyword[-1] + dtc_keyword_list[level][idx]
                elif dtc_keyword[-1] == '#':
                    tmp_dtc_keyword = dtc_keyword[:-1] + '$#' + dtc_keyword_list[level][idx]
                else:
                    tmp_dtc_keyword = dtc_keyword + '$' + dtc_keyword_list[level][idx]
                self.vec_word_combine(tmp_list, category, tmp_dtc_keyword, dtc_keyword_list, level + 1, hmd_rule)
        return tmp_list

    def load_hmd_model(self, category_delimiter, model_name):
        """
        Load HMD model
        :param      category_delimiter:     HMD category delimiter
        :param      model_name:             Model name
        :return:                            HMD dictionary
        """
        try:
            hm = self.load_model(model_name)
            # Make HMD matrix list
            matrix_list = list()
            for rules in hm.rules:
                dtc_keyword_list = list()
                rule_list = self.split_hmd_rule(rules.rule)
                for idx in range(len(rule_list)):
                    dtc_keyword = rule_list[idx].split('|')
                    dtc_keyword_list.append(dtc_keyword)
                tmp_list = list()
                category = category_delimiter.join(rules.categories)
                matrix_list += self.vec_word_combine(tmp_list, category, '', dtc_keyword_list, 0, rules.rule)
            # Make HMD matrix dictionary
            hmd_dict = dict()
            for category, dtc_keyword, hmd_rule in matrix_list:
                if len(category) < 1 or category.startswith('#') or len(dtc_keyword) < 1:
                    continue
                if dtc_keyword not in hmd_dict:
                    hmd_dict[dtc_keyword] = [[category, hmd_rule]]
                else:
                    hmd_dict[dtc_keyword].append([category, hmd_rule])
            return hmd_dict
        except Exception:
            raise Exception(traceback.format_exc())

    @staticmethod
    def find_loc(space_idx_list, pos, plus_num, len_nlp_sent):
        s_i = 0
        len_vs = len(space_idx_list)
        for s_i in range(len_vs):
            if space_idx_list[s_i] > pos:
                break
        key_pos = space_idx_list[s_i]
        if s_i != -1:
            e_i = s_i + plus_num
            if e_i >= len_vs:
                e_i = len_vs - 1
            end_pos = space_idx_list[e_i] + 1
        else:
            end_pos = len_nlp_sent
        return key_pos, end_pos

    def find_hmd(self, dtc_word_list, sentence, tmp_nlp_sent, space_idx_list):
        pos = 0
        output_nlp_sent = ''
        for dtc_word in dtc_word_list:
            if len(dtc_word) == 0:
                continue
            b_pos = True
            b_sub = False
            b_neg = False
            key_pos = 0
            end_pos = len(tmp_nlp_sent)
            # Searching Special Command
            w_loc = -1
            while True:
                w_loc += 1
                if w_loc == len(dtc_word):
                    return tmp_nlp_sent.strip(), False
                if dtc_word[w_loc] == '!':
                    if b_pos:
                        b_pos = False
                    else:
                        b_neg = True
                elif dtc_word[w_loc] == '@':
                    key_pos = pos
                elif dtc_word[w_loc] == '+':
                    w_loc += 1
                    try:
                        plus_num = int(dtc_word[w_loc]) + len(dtc_word.strip().split(' ')) - 1
                        key_pos, end_pos = self.find_loc(space_idx_list, pos, plus_num, len(tmp_nlp_sent))
                    except ValueError:
                        return tmp_nlp_sent.strip(), False
                elif dtc_word[w_loc] == '%':
                    b_sub = True
                else:
                    k_str = dtc_word[w_loc:]
                    break
            # Searching lemma
            t_pos = 0
            if b_pos:
                if b_sub:
                    pos = tmp_nlp_sent[key_pos:end_pos].find(k_str)
                else:
                    pos = tmp_nlp_sent[key_pos:end_pos].find(' ' + k_str + ' ')
                if pos != -1:
                    pos = pos + key_pos
            else:
                t_pos = key_pos
                if b_neg:
                    pos = sentence.find(k_str)
                elif b_sub:
                    pos = tmp_nlp_sent[key_pos:end_pos].find(k_str)
                else:
                    pos = tmp_nlp_sent[key_pos:end_pos].find(' ' + k_str + ' ')
            # Checking Result
            if b_pos:
                if pos > -1:
                    if b_sub:
                        replace_str = ''
                        for item in k_str:
                            replace_str += ' ' if item == ' ' else '_'
                        output_nlp_sent = tmp_nlp_sent[:key_pos]
                        output_nlp_sent += tmp_nlp_sent[key_pos:end_pos].replace(k_str, replace_str)
                        output_nlp_sent += tmp_nlp_sent[end_pos:]
                    else:
                        target_str = ' ' + k_str + ' '
                        replace_str = ''
                        for item in k_str:
                            replace_str += ' ' if item == ' ' else '_'
                        replace_str = ' ' + replace_str + ' '
                        output_nlp_sent = tmp_nlp_sent[:key_pos]
                        output_nlp_sent += tmp_nlp_sent[key_pos:end_pos].replace(target_str, replace_str)
                        output_nlp_sent += tmp_nlp_sent[end_pos:]
                else:
                    return tmp_nlp_sent.strip(), False
            else:
                if pos > -1:
                    return tmp_nlp_sent.strip(), False
                else:
                    pos = t_pos
        return output_nlp_sent.strip(), True

    def execute_hmd(self, sent, nlp_sent, hmd_dict):
        detect_category_dict = dict()
        tmp_nlp_sent = ' {0} '.format(nlp_sent)
        tmp_nlp_sent = tmp_nlp_sent.decode('utf-8')
        space_idx_list = [idx for idx in range(len(tmp_nlp_sent)) if tmp_nlp_sent.startswith(' ', idx)]
        if hmd_dict:
            for dtc_keyword in hmd_dict.keys():
                dtc_word_list = dtc_keyword.split('$')
                output_nlp_sent, b_print = self.find_hmd(dtc_word_list, sent, tmp_nlp_sent, space_idx_list)
                if b_print:
                    for category, hmd_rule in hmd_dict[dtc_keyword]:
                        if category not in detect_category_dict:
                            detect_category_dict[category] = [(dtc_keyword, hmd_rule, output_nlp_sent)]
                        else:
                            detect_category_dict[category].append((dtc_keyword, hmd_rule, output_nlp_sent))
        return detect_category_dict

    def del_hmd_model(self, model_name):
        model_path = '{0}/{1}__0.hmdmodel'.format(self.conf.get('brain-ta.hmd.model.dir'), model_name)
        if os.path.exists(model_path):
            os.remove(model_path)

    def hmd_model_path(self, model_name):
        model_path = '{0}/{1}__0.hmdmodel'.format(self.conf.get('brain-ta.hmd.model.dir'), model_name)
        return model_path


class NlpApi(Resource):
    def __init__(self):
        self.json_data = request.get_json(silent=True, cache=False, force=True)
        print(self.json_data)
        self.target_str = self.json_data.get('target_str')
        self.uni_id = self.json_data.get('uni_id')
        self.nlp_engn = self.json_data.get('nlp_engn') if self.json_data.get('nlp_engn') else 'nlp3'

    def post(self):
        return nlp_main(self.target_str, self.uni_id, self.nlp_engn)


class HmdApi(Resource):
    def __init__(self):
        self.json_data = request.get_json(silent=True, cache=False, force=True)
        print(self.json_data)
        self.target_str = self.json_data.get('target_str')
        self.uni_id = self.json_data.get('uni_id')
        self.nlp_engn = self.json_data.get('nlp_engn') if self.json_data.get('nlp_engn') else 'nlp3'
        self.hmd_info = self.json_data.get('hmd_info') if self.json_data.get('hmd_info') else False

    def post(self):
        return hmd_main(self.target_str, self.uni_id, self.nlp_engn, self.hmd_info)


#######
# def #
#######
def check_process(pro_name):
    """
    Extract number of processes running
    @param      pro_name:   Process name
    @return:                Number of processes running
    """
    pro_list = subprocess.check_output(['ps', 'uaxw']).splitlines()
    pro_cnt = len([pro for pro in pro_list if pro_name in pro])
    return pro_cnt


def check_supervisor():
    """
    Check Supervisor status
    @return:        Supervisor status
    """
    sub_pro = subprocess.Popen('/engn/maum/bin/svctl status', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    response_out, response_err = sub_pro.communicate()
    return response_out.strip()


def cancel_reservation(db, cust_tel_no, call_time):
    """
    Check Supervisor status
    :param      db:                 MYSQL DB
    :param      cust_tel_no:        Cust Telephone Number
    :param      call_time:          Call Time
    @return:                        Supervisor status
    """
    # 인자값 확인.
    modify_cust_tel_no = '9{0}'.format(cust_tel_no)
    if len(call_time) != 12:
        return {'result': -1, 'detail': 'call time length is not 12'}
    # contract_no 조회
    results = util.select_contract_no(
        db=db,
        cust_tel_no=modify_cust_tel_no,
        call_time=call_time
    )
    if not results:
        return {'result': -1, 'detail': 'reservation does not exists or call_number is already masking'}
    # call_try_count 값 변경.
    for result in results:
        if str(result['CALL_TRY_COUNT']) == '1':
            return {'result': -1, 'detail': 'Call is Already executed'}
        if str(result['CALL_TRY_COUNT']) == '-1':
            return {'result': -1, 'detail': 'Call is Already Canceled'}
        util.update_call_try_count(
            db=db,
            contract_no=result['CONTRACT_NO']
        )
    return {'result': 0, 'detail': 'SUCCESS'}


def nlp_main(target_str, uni_id, nlp_engn):
    """
    This is a program that NLP API
    @param      target_str:     Target string
    @param      uni_id:         Unique ID
    @param      nlp_engn:       NLP engine(NLP1, NLP2, NLP3)
    @return:
    """
    flag = False
    output_dict = {'uni_id': uni_id, 'output': list()}
    for _ in range(0, 3):
        try:
            log_str_list = list()
            start_time = datetime.now()
            nlp_client = NlpClient(nlp_engn)
            target_str = target_str.strip()
            target_str_list = target_str.replace("\r\n", "\n").split("\n")
            log_str = """
                Requests time = {0}
                uni_id        = {1}
                nlp_engn      = {2}
                target_str    = {3}""".format(start_time, uni_id, nlp_engn, target_str)
            log_str_list.append(log_str)
            cnt = 1
            for target_sent in target_str_list:
                if len(target_sent) < 1:
                    continue
                target_text, nlp_sent, morph_sent = nlp_client.analyze(target_sent)
                hmd_sample_list = list()
                morph_sent_list = morph_sent.split()
                for item in morph_sent_list:
                    item_list = item.split('/')
                    if len(item_list) == 2:
                        word = item_list[0]
                        morph = item_list[1]
                    else:
                        word = '/'
                        morph = item_list[1]
                    if morph in ['VV', 'VA', 'VX', 'VCP', 'VCN', 'NNG', 'NNP'] and len(word) >= 6:
                        hmd_word = "({0})".format(word)
                        if hmd_word in hmd_sample_list:
                            continue
                        hmd_sample_list.append(hmd_word)
                output_dict['output'].append(
                    {'nlp_sent': nlp_sent, 'morph_sent': morph_sent, 'hmd_sample': ''.join(hmd_sample_list)}
                )
                log_str = """
                    {0})
                        target_sent   = {1}
                        nlp_sent      = {2}
                        morph_sent    = {3}
                        hmd_sample    = {4}""".format(
                    cnt, target_sent, nlp_sent, morph_sent, ''.join(hmd_sample_list))
                log_str_list.append(log_str)
                cnt += 1
            log_str = """
                required_time = {0}""".format((datetime.now() - start_time))
            log_str_list.append(log_str)
            print(''.join(log_str_list))
            print('-' * 100)
            flag = True
            break
        except Exception:
            print(traceback.format_exc())
            print('-' * 100)
            pass
    if not flag:
        print('uni_id = {0} \n{1}'.format(uni_id, traceback.format_exc()))
        print('-' * 100)
        return -1
    return output_dict


def hmd_main(target_str, uni_id, nlp_engn, hmd_info):
    """
    This is a program that HMD API
    @param      target_str:     Target string
    @param      uni_id:         Unique ID
    @param      nlp_engn:       NLP engine(NLP1, NLP2, NLP3)
    @param      hmd_info:       HMD dictionary [{'cate': '', 'rule': ''}, ....]
    @return:
    """
    flag = False
    output_dict = {'uni_id': uni_id, 'output': list()}
    for _ in range(0, 3):
        try:
            log_str_list = list()
            start_time = datetime.now()
            target_str = target_str.strip()
            target_str_list = target_str.replace("\r\n", "\n").split("\n")
            # Make HMD model
            hmd_model_list = list()
            hmd_info_str_list = list()
            for item in hmd_info:
                hmd_model_list.append(([item['cate'], ], item['rule']))
                hmd_info_str_list.append("[cate: {0}, rule: {1}]".format(item['cate'], item['rule']))
            log_str = """
                Requests time = {0}
                uni_id        = {1}
                nlp_engn      = {2}
                target_str    = {3}
                hmd_info      = {4}""".format(
                start_time, uni_id, nlp_engn, target_str, ','.join(hmd_info_str_list))
            log_str_list.append(log_str)
            hmd_client = HmdClient()
            hmd_client.set_model(uni_id, hmd_model_list)
            hmd_model = hmd_client.load_hmd_model("!@#$", uni_id)
            nlp_client = NlpClient(nlp_engn)
            # HMD
            cnt = 1
            overlap_dict = dict()
            for target_sent in target_str_list:
                if len(target_sent) < 1:
                    continue
                target_text, nlp_sent, morph_sent = nlp_client.analyze(target_sent)
                dtc_cat_result = hmd_client.execute_hmd(target_text, nlp_sent, hmd_model)
                if dtc_cat_result:
                    for dtc_cate, value_list in dtc_cat_result.items():
                        for value in value_list:
                            dtct_kwd = value[0]
                            hmd_rule = value[1]
                            overlap_key = "{0}\t{1}\t{2}\t{3}".format(dtc_cate, target_sent, dtct_kwd, hmd_rule)
                            if overlap_key in overlap_dict:
                                continue
                            overlap_dict[overlap_key] = 1
                            output_info = {
                                'cate': dtc_cate,
                                'sent': target_sent,
                                'nlp_sent': nlp_sent,
                                'dtct_kwd': dtct_kwd,
                                'hmd_rule': hmd_rule
                            }
                            output_dict['output'].append(output_info)
                            log_str = """
                            {0})
                                cate          = {1}
                                target_sent   = {2}
                                nlp_sent      = {3}
                                dtct_kwd      = {4}
                                hmd_rule      = {5}""".format(
                                cnt, dtc_cate, target_sent, nlp_sent, dtct_kwd, hmd_rule)
                            log_str_list.append(log_str)
                            cnt += 1
            hmd_client.del_hmd_model(uni_id)
            log_str = """
                required_time = {0}""".format((datetime.now() - start_time))
            log_str_list.append(log_str)
            print(''.join(log_str_list))
            print('-' * 100)
            flag = True
            break
        except Exception:
            print(traceback.format_exc())
            print('-' * 100)
            pass
    if not flag:
        print('uni_id = {0} \n'.format(uni_id) + traceback.format_exc())
        print('-' * 100)
        return -1
    return output_dict


# Flask 인스턴스 생성
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
CORS(app)
api = Api(app)
parser = reqparse.RequestParser()
parser.add_argument('pro_name', type=str)
parser.add_argument('target_str', type=str)
parser.add_argument('uni_id', type=str)
parser.add_argument('nlp_engn', type=str)
parser.add_argument('hmd_info', type=list, required=False)
parser.add_argument('cust_tel_no', type=str)
parser.add_argument('call_time', type=str)
api.add_resource(NlpApi, '/nlp')
api.add_resource(HmdApi, '/hmd')
api.add_resource(CheckProAPI, '/check_pro')
api.add_resource(CheckSupervisorAPI, '/check_svctl')
api.add_resource(CallReservationCancel, '/call_rsvt_cncl')

