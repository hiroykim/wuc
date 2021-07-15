#!/usr/bin/python
# -*- coding: utf-8 -*-

"""program"""
__author__ = "MINDsLAB"
__date__ = "creation: 2019-02-14, modification: 0000-00-00"

###########
# imports #
###########
import os
import re
import sys
import time
import argparse
import traceback
import collections
from datetime import datetime

###########
# options #
###########
reload(sys)
sys.setdefaultencoding("utf-8")

#############
# constants #
#############
RE_RULE = {
    'number_rule': r'((0|1|2|3|4|5|6|7|8|9|(?:10)|일|(?:하나)|이|둘|삼|사|오|육|륙|일곱|칠|여덟|팔|아홉|구|공|넷|셋|영|십|백)\s?){2,}',
    'birth_rule': r'((0|1|2|3|4|5|6|7|8|9|(?:10)|일|(?:하나)|이|둘|삼|사|오|육|륙|칠|팔|구|공|넷|영|십|년|월|백|천|시)\s?){3,}',
    'email_rule': r'(.\s?){4}((?:골\s?뱅\s?이)|(?:닷\s?컴)|("?:다\s?컴)|(?:닷\s?넷)|(?:닷\s?케\s?이\?알)|(?:한메일)|(?:지메일)|(?:쥐메일)|(?:핫메일))',
    'address_rule': r'\s((.){2}시)|\s((.){2}구)|\s((.){1,4}동)|((?:빌딩)|(?:아파트)|(?:번지)|(?:빌라)|길|읍)',
    'alphabet_rule': r'(?:(에이|비|씨|디|이|에프|쥐|에이치|아이|제이|케이|엘|엠|엔|오|피|큐|알|에스|티|유|브이|더블유|엑스|와이|지)\s?){3,}',
    'name_rule': r'(?:(가|간|갈|감|강|개|견|경|계|고|곡|공|곽|교|구|국|군|궁|궉|권|근|금|기|길|김|나|라|남|(?:남궁)|낭|랑|내|노|로|뇌|누|단|담|당|대|도|(?:독고)|돈|동|(?:동방)|두|라|류|마|망|절|매|맹|먕|모|묘|목|묵|문|미|민|박|반|방|배|백|범|변|복|봉|부|빈|빙|사|(?:사공)|삼|상|서|(?:서문)|석|선|(?:선우)|설|섭|성|소|(?:소봉)|손|송|수|순|숭|시|신|심|십|아|안|애|야|양|량|어|(?:어금)|엄|여|연|염|영|예|오|옥|온|옹|왕|요|용|우|운|원|위|유|육|윤|은|음|이|인|임|림|자|장|전|점|정|제|(?:제갈)|조|종|좌|주|준|즙|지|진|차|창|채|척|천|초|최|추|축|춘|탁|탄|태|판|패|편|평|포|표|퐁|피|필|하|학|한|함|해|허|현|형|호|홍|화|환|황|(?:황보))\s?[(가-힐)](\s?[(가-힐)]))'
}


#######
# def #
#######
def elapsed_time(start_time):
    """
    elapsed time
    :param          start_time:          date object
    :return                              Required time (type : datetime)
    """
    end_time = datetime.fromtimestamp(time.time())
    required_time = end_time - start_time
    return required_time


def detected_rule(line, rule_code, word_list, re_rule_dict):
    """
    Detecting re rule
    :param      line:               Line
    :param      rule_code:          Rule code
    :param      word_list:          Search word list
    :param      re_rule_dict:       re rule dictionary
    :return:                        re rule dictionary
    """
    rule_code_dict = {
        'name_rule': RE_RULE['name_rule'],
        'id_rule': RE_RULE['alphabet_rule'],
        'tel_number_rule': RE_RULE['number_rule'],
        'card_number_rule': RE_RULE['number_rule'],
        'id_number_rule': RE_RULE['number_rule'],
        'account_number_rule': RE_RULE['number_rule'],
        'address_rule': RE_RULE['address_rule'],
        'birth_rule': RE_RULE['birth_rule']
    }
    for word in word_list:
        if word in line:
            re_rule_dict[rule_code] = rule_code_dict[rule_code]
            return re_rule_dict
    return re_rule_dict


def masking(input_line_list, encoding):
    """
    Masking
    :param      input_line_list:    Input line list
    :param      encoding:           String encoding
    :return:                        Output dictionary and index output dictionary
    """
    word_list_fir = [u'맞으', u'어떻게', u'말씀', u'맞습', u'불러', u'확인']
    word_list_sec = [u'확인', u'어떻게', u'말씀', u'부탁', u'여쭤', u'맞으', u'이요', u'불러', u'남겨', u'구요']
    non_masking_word = [
        u'고객님', u'맞', u'본인', u'여권번호', u'감사합', u'확인', u'아니요', u'잠시만요',
        u'음', u'어', u'위해', u'지금', u'주문', u'말씀', u'여권', u'번호', u'또는', u'사용하시는',
        u'사용하는', u'아이디', u'십니까', u'성함', u'롯데', u'면세점', u'개인', u'부분', u'포인트',
        u'소중한', u'개인정보', u'모레', u'아침', u'이메일', u'동의', u'잠시만'
    ]
    precent_undetected = [u'네', u'네네', u'네네네', u'아', u'어', u'잠시만요', u'잠깐만요', u'예', u'예예']
    # 1. Extract target line
    line_cnt = 0
    line_dict = collections.OrderedDict()
    for line in input_line_list:
        line = line.strip()
        try:
            line_dict[line_cnt] = line.decode(encoding)
        except Exception:
            if line[-1] == '\xb1':
                line_dict[line_cnt] = line[:-1].decode(encoding)
        line_cnt += 1
    # 2. Detecting re rule
    next_line_cnt = 2
    minimum_length = 3
    line_re_rule_dict = collections.OrderedDict()
    for line_num, line in line_dict.items():
        re_rule_dict = dict()
        self_re_rule_dict = dict()
        detect_line = False
        # Name rule
        if u'성함' in line or u'이름' in line:
            re_rule_dict = detected_rule(line, 'name_rule', word_list_sec, re_rule_dict)
        if u'본인' in line:
            for word in [u'가요', u'맞으', u'세요', u'니까']:
                if word in line:
                    # self_re_rule_dict['me_name_rule'] = RE_RULE['name_rule']
                    detect_line = True
                    break
        # ID rule
        if u'아이디' in line:
            re_rule_dict = detected_rule(line, 'id_rule', word_list_fir, re_rule_dict)
        # Tell number rule
        if u'핸드폰' in line and u'번호' in line:
            re_rule_dict = detected_rule(line, 'tel_number_rule', word_list_sec, re_rule_dict)
        for item in [u'휴대폰', u'전화', u'팩스', u'연락처']:
            if item in line:
                re_rule_dict = detected_rule(line, 'tel_number_rule', word_list_sec, re_rule_dict)
                detect_line = True
                break
        # Card number rule
        if u'카드' in line and u'번호' in line:
            re_rule_dict = detected_rule(line, 'card_number_rule', word_list_sec, re_rule_dict)
        # ID number rule
        if u'주민' in line and u'번호' in line and u'앞자리' in line:
            re_rule_dict['id_number_rule'] = RE_RULE['birth_rule']
        if u'번호' in line:
            for item in [u'주민', u'면허', u'여권']:
                if item in line:
                    re_rule_dict = detected_rule(line, 'id_number_rule', word_list_sec, re_rule_dict)
                    break
            if u'외국인' in line and u'등록' in line:
                re_rule_dict = detected_rule(line, 'id_number_rule', word_list_sec, re_rule_dict)
        # Account number rule
        bank_list = [
            u'신한', u'농협', u'우리', u'하나', u'기업', u'국민', u'외환', u'씨티',
            u'수협', u'대구', u'부산', u'광주', u'제주', u'전북', u'경남', u'케이',
            u'카카오'
        ]
        for bank_name in bank_list:
            if bank_name in line:
                if u'은행' in line or u'뱅크' in line:
                    re_rule_dict['account_number_rule'] = RE_RULE['number_rule']
        if u'계좌' in line and u'번호' in line:
            re_rule_dict = detected_rule(line, 'account_number_rule', word_list_sec, re_rule_dict)
        # Email rule
        if u'이메일' in line and u'주소' in line:
            re_rule_dict['email_rule'] = RE_RULE['email_rule']
        # Address rule
        if u'주소' in line:
            re_rule_dict = detected_rule(line, 'address_rule', word_list_sec, re_rule_dict)
        # Birth rule
        if u'생년월일' in line:
            re_rule_dict = detected_rule(line, 'birth_rule', word_list_sec, re_rule_dict)
        # 특이케이스 마스킹 탐지 발화 문장 포함
        if detect_line:
            if line_num not in line_re_rule_dict:
                line_re_rule_dict[line_num] = dict()
            line_re_rule_dict[line_num].update(self_re_rule_dict)
            line_re_rule_dict[line_num].update(re_rule_dict)
        #
        for next_line_num in range(line_num + 1, len(line_dict)):
            if next_line_num in line_dict:
                for word in precent_undetected:
                    if word == line_dict[next_line_num].replace(' ', ''):
                        next_line_cnt += 1
                        break
                if next_line_num not in line_re_rule_dict:
                    line_re_rule_dict[next_line_num] = dict()
                line_re_rule_dict[next_line_num].update(re_rule_dict)
                next_line_cnt -= 1
                if next_line_cnt <= 0:
                    break
    # 3. Extract masking
    output_dict = collections.OrderedDict()
    index_output_dict = collections.OrderedDict()
    for re_line_num, re_rule_dict in line_re_rule_dict.items():
        output_str = ''
        if len(line_dict[re_line_num]) < int(minimum_length):
            output_dict[re_line_num] = line_dict[re_line_num].encode(encoding)
            index_output_dict[re_line_num] = list()
            continue
        for rule_name, re_rule in re_rule_dict.items():
            if rule_name in ['name_rule', 'birth_rule', 'id_rule', 'me_name_rule']:
                masking_cnt = 2
            elif rule_name in ['tel_number_rule', 'id_number_rule', 'card_number_rule', 'account_number_rule']:
                masking_cnt = 2
            elif rule_name in ['address_rule', 'email_rule']:
                masking_cnt = 3
            else:
                masking_cnt = 3
            p = re.compile(re_rule.decode('utf-8'))
            re_result = p.finditer(line_dict[re_line_num].decode('utf-8'))
            if len(output_str) < 1:
                output_str = line_dict[re_line_num].decode('utf-8')
            index_info = list()
            for item in re_result:
                idx_tuple = item.span()
                start = idx_tuple[0]
                end = idx_tuple[1]
                masking_part = ""
                index_info.append(
                    {"start_idx": start, "end_idx": end, "rule_name": rule_name}
                )
                cnt = 0
                # 이름 규칙 룰에 적용되면서 띄어쓰기(공백)가 존재할시 생략
                if (rule_name == 'name_rule' or rule_name == 'me_name_rule') and ' ' in output_str[start:end]:
                    continue
                word_idx_list = list()
                for word in non_masking_word:
                    temp_start = start - 3 if start - 3 > 0 else 0
                    if word in output_str[temp_start:end + 3] or output_str in word:
                        word_start_idx = temp_start + output_str[temp_start:end + 3].find(word) - start
                        word_end_idx = word_start_idx + len(word)
                        word_idx_list.append(range(word_start_idx, word_end_idx))
                for idx in output_str[start:end]:
                    if idx == " ":
                        masking_part += " "
                        continue
                    cnt += 1
                    if cnt % masking_cnt == 0:
                        masking_part += idx
                    else:
                        flag = False
                        for idx_range in word_idx_list:
                            if cnt - 1 in idx_range:
                                flag = True
                                masking_part += idx
                                break
                        if not flag:
                            masking_part += "*"
                output_str = output_str.replace(output_str[start:end], masking_part)
            if re_line_num not in index_output_dict:
                index_output_dict[re_line_num] = index_info
            else:
                for data in index_info:
                    index_output_dict[re_line_num].append(data)
        if len(output_str) > 1:
            output_dict[re_line_num] = output_str.encode(encoding)
    return output_dict, index_output_dict


def main(args):
    """
    This is a program that masking
    """
    pro_st = datetime.fromtimestamp(time.time())
    try:
        if args.input_file_path:
            if not os.path.exists(args.input_file_path):
                raise Exception("Can't find input file")
            input_file = open(args.input_file_path)
            input_line_list = input_file.readlines()
            input_file.close()
            output_dict, index_output_dict = masking(input_line_list, args.encoding)
            output_file = open("{0}_masking_output".format(args.input_file_path), 'w')
            for line_num in range(0, len(input_line_list)):
                if line_num in output_dict:
                    print >> output_file, output_dict[line_num]
                else:
                    print >> output_file, input_line_list[line_num].strip()
            output_file.close()
        elif args.input_dir_path:
            if os.path.isabs(args.input_dir_path):
                input_dir_path = args.input_dir_path
            else:
                input_dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), args.input_dir_path)
            if not os.path.exists(input_dir_path):
                raise Exception("Can't find directory")
            w_ob = os.walk(input_dir_path)
            for dir_path, sub_dirs, files in w_ob:
                for file_name in files:
                    try:
                        input_file = open(os.path.join(dir_path, file_name))
                        input_line_list = input_file.readlines()
                        input_file.close()
                        output_dict, index_output_dict = masking(input_line_list, args.encoding)
                        output_file = open("{0}_masking_output".format(os.path.join(dir_path, file_name)), 'w')
                        for line_num in range(0, len(input_line_list)):
                            if line_num in output_dict:
                                print >> output_file, output_dict[line_num]
                            else:
                                print >> output_file, input_line_list[line_num].strip()
                        output_file.close()
                    except Exception:
                        print(traceback.format_exc())
                        print("Masking Error {0}".format(os.path.join(dir_path, file_name)))
                        continue
        print("[E N D] Start time = {0}, The time required = {1}".format(pro_st, elapsed_time(pro_st)))
    except Exception:
        print(traceback.format_exc())
        print("[FAIL] Start time = {0}, The time required = {1}".format(pro_st, elapsed_time(pro_st)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', action='store', dest='input_dir_path', default=False, type=str,
                        help='Input directory path')
    parser.add_argument('-f', action='store', dest='input_file_path', default=False, type=str,
                        help='Input file path')
    parser.add_argument('-e', action='store', dest='encoding', default="utf-8", type=str,
                        help='File encoding format [default = utf-8]')
    arguments = parser.parse_args()
    main(arguments)
