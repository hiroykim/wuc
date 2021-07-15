#!/usr/bin/python
# -*- coding:utf-8 -*-

"""program"""
__author__ = "MINDsLAB"
__date__ = "creation: 2018-08-24, modification: 2020-12-11"

###########
# imports #
###########
import os
import sys
import grpc
import json
import argparse
from google.protobuf import json_format
sys.path.append('/APP/maum/lib')
import py3_nlp
sys.path.append(os.path.join(os.getenv('MAUM_ROOT'), 'lib/python'))
from common.config import Config
from maum.common import lang_pb2
from maum.brain.hmd import hmd_pb2, hmd_pb2_grpc


#########
# class #
#########
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


#######
# def #
#######
def main(args):
    """
    This is a program that execute HMD
    @param      args:     Arguments
    """
    hmd_file = open(args.hmd_file)
    # Make HMD model
    hmd_model_list = list()
    hmd_line_num = 0
    for line in hmd_file:
        hmd_line_num += 1
        line = line.strip()
        line_list = line.split('\t')
        if len(line_list) != 2:
            print("[ERROR] Line number {0} isn't two column".format(hmd_line_num))
            continue
        cate, rule = line_list
        hmd_model_list.append(([cate, ], rule))
    hmd_client = HmdClient()
    hmd_client.set_model(args.hmd_file, hmd_model_list)
    hmd_file.close()
    # Execute HMD
    overlap_dict = dict()
    target_file = open(args.input_file)
    output_file = open(args.input_file + '_output', 'w')
    nlp_client = py3_nlp.NlpClient(args.nlp_vs)
    for line in target_file:
        target_sent = line.strip()
        if len(target_sent) < 1:
            continue
        target_text, nlp_sent, morph_sent = nlp_client.analyze(target_sent)
        dtc_cat_result = hmd_client.execute_hmd(target_text, nlp_sent, hmd_model)
        if dtc_cat_result:
            for dtc_cate, value_list in dtc_cat_result.items():
                for value in value_list:
                    dtct_kwd = value[0]
                    hmd_rule = value[1]
                    overlap_key = "{0}\t{1}\t{2}\t{3}".format(dtc_cate, target_text, dtct_kwd, hmd_rule)
                    if overlap_key in overlap_dict:
                        continue
                    overlap_dict[overlap_key] = 1
                    print("{0}\t{1}\t{2}\t{3}\t{4}".format(dtc_cate, target_text, nlp_sent, dtct_kwd, hmd_rule))
                    print("{0}\t{1}\t{2}\t{3}\t{4}".format(
                        dtc_cate, target_text, nlp_sent, dtct_kwd, hmd_rule), file=output_file)
        else:
            print("None\t{0}\t{1}\tNone\tNone".format(target_text, nlp_sent))
            print("None\t{0}\t{1}\tNone\tNone".format(target_sent, nlp_sent), file=output_file)
    hmd_client.del_hmd_model(args.hmd_file)
    target_file.close()
    output_file.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-i', nargs='?', action='store', dest='input_file', required=True,
                        help="Input target text file")
    parser.add_argument('-t', nargs='?', action='store', dest='hmd_file', required=True,
                        help="Input HMD file")
    parser.add_argument('-e', nargs='?', action='store', dest='nlp_vs', default='nlp3',
                        help="Choose NLP engine version [Default= nlp3]\n[ex) nlp1 / nlp2 / nlp3 ]")
    arguments = parser.parse_args()
    main(arguments)
