#!/usr/bin/python
# -*- coding:utf-8 -*-

"""program"""
__author__ = "MINDsLAB"
__date__ = "creation: 2018-08-24, modification: 2019-02-16"

###########
# imports #
###########
import os
import sys
import grpc
import time
import argparse
import traceback
from datetime import datetime
sys.path.append(os.path.join(os.getenv('MAUM_ROOT'), 'lib/python'))
from common.config import Config
from maum.common import lang_pb2
from maum.brain.nlp import nlp_pb2, nlp_pb2_grpc


#########
# class #
#########
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
        in_text.text = target_text.replace('*', ' ')
        in_text.lang = lang_pb2.kor
        in_text.split_sentence = False
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
#            text = ret.sentences[idx].text
            analysis = ret.sentences[idx].morps
            for ana_idx in range(len(analysis)):
                morphs_word = analysis[ana_idx].lemma
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


########
# main #
########
def main(args):
    """
    This program that NLP test
    :param      args:       Arguments
    """
    if args.mode == 0:
        try:
            test_sent = '이 문장은 테스트 문장입니다.'
            nlp_client = NlpClient(args.engine)
            result = nlp_client.analyze(test_sent)
            if result:
                print('Connect succeed')
        except Exception:
            print('Connect failed')
            sys.exit(1)
    elif args.mode == 1:
        try:
            if not args.sent:
                print("[ERROR] Input target sentence")
                sys.exit(1)
            nlp_client = NlpClient(args.engine)
            target_text, nlp_sent, morph_sent = nlp_client.analyze(args.sent)
            print(nlp_sent)
        except Exception:
            print("[ERROR] Can't recognize")
            sys.exit(1)
    elif args.mode == 2:
        try:
            if not args.sent:
                print("[ERROR] Input target sentence")
                sys.exit(1)
            nlp_client = NlpClient(args.engine)
            target_text, nlp_sent, morph_sent = nlp_client.analyze(args.sent)
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
                if morph in ['VV', 'VA', 'VX', 'VCP', 'VCN', 'NNG', 'NNP'] and len(word) >= 2:
                    hmd_word = "({0})".format(word)
                    if hmd_word in hmd_sample_list:
                        continue
                    hmd_sample_list.append(hmd_word)
            print(''.join(hmd_sample_list))
        except Exception:
            print("[ERROR] Can't recognize")
            sys.exit(1)
    else:
        print("[ERROR] Wrong script mode")
        print("""Choose script mode
    0 : Check NLP engine
    1 : Simple NLP test
    2 : Make HMD sample""")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-m', nargs='?', action='store', dest='mode', required=True, type=int, help="""
    0 : Check NLP engine
    1 : Simple NLP test
    2 : Make HMD sample""")
    parser.add_argument('-e', nargs='?', action='store', dest='engine', required=True,
                        help="Choose NLP engine version\n[ex) nlp1 / nlp2 / nlp3 ]")
    parser.add_argument('-s', nargs='?', action='store', dest='sent', default=False,
                        help="Input target sentence\n[ex) '이 문장은 테스트 문장입니다.']")
    arguments = parser.parse_args()
    main(arguments)
