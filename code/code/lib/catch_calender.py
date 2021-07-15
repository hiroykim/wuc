#!/usr/bin/python
# -*- coding: utf-8 -*-

"""program"""
__author__ = "MINDsLAB"
__date__ = "creation: 2021-06-15, modification: 0000-00-00"

###########
# imports #
###########
import re
import argparse


#########
# class #
#########
class CatchCalender:
    def __init__(self):
        reg_list = list()
        reg_list.append(r'(한|두|세|네|다섯|여섯|일곱|여덟|아홉|열){1,2}시')
        reg_list.append(r'(십이|십삼|십사|십오|십육|십칠|십팔|십구|이십|이십일|이십이|이십삼|이십사){1,4}시')
        reg_list.append(r'(월|화|수|목|금|토|일)요일')
        reg_list.append(r'(이번|다음|다다음|차|금){1,3}주.*(다시|전화|걸어|주세요|해주|연락|통화|가능|시|요일|오전|오후|저녁|아침|퇴근|밤|자정)')
        reg_list.append(r'(있다가|일단|있다|이따|이따가|오늘|내일|내일모레|모레|글피).*(전화|연락|통화|해주|가능|걸어|주세요|시|요일|오전|오후|저녁|아침|퇴근|밤|자정)')
        reg_list.append(r'(언제).*(전화|연락|통화|가능).*')
        reg_list.append(r'(언제).*(주시|주실|줄 거|걸어|주세요|주는|줄 건|오는|올 건).*')
        reg_list.append(r'(예약).*(어떻게|언제).*')
        reg_list.append(r'(정도).*(전화|연락|통화|시간).*(같아|같습|같은|날것|주시|주실|줄 거|걸어|주세요)')
        reg_list.append(r'오전|오후|저녁|아침|퇴근|점심|밤|자정')
        reg_list.append(r'(0|1|2|3|4|5|6|7|8|9|10|11|12|13|14|15|16|17|18|19|20|21|22|23|24|일|'
                        r'한|두|둘|셋|세|삼|사|네|오|다섯|육|륙|여섯|칠|일곱|팔|여덟|구|아홉|공|넷|영|십|열|이){1,2}시간\w?(뒤|후)')
        reg_list.append(r'(0|1|2|3|4|5|6|7|8|9|10|11|12|13|14|15|16|17|18|19|20|21|22|23|24|일|'
                        r'한|두|둘|셋|세|삼|사|네|오|다섯|육|륙|여섯|칠|일곱|팔|여덟|구|아홉|공|넷|영|십|열|이){1,2}분\w?(뒤|후)')
        reg_list.append(r'(하루|이틀|사흘|나흘|닷세|엿세|이레|여드레|나흐레|열흘|잠시|며칠|몇일){1,3}(뒤|후)')
        self.reg_compile_list = list()
        for reg_str in reg_list:
            self.reg_compile_list.append(re.compile(reg_str))

    def catch_calender_text(self, text):
        """
        Catch Calender Text
        :param      text:       Text
        :return:                Output Text
        """
        unicode_text = text
        find_text_list = list()
        for reg_compile in self.reg_compile_list:
            iter_result = reg_compile.finditer(unicode_text)
            for value in iter_result:
                idx_start = value.start()
                idx_end = value.end()
                find_text_list.append((idx_start, idx_end))
        index_dict = dict()
        for idx_start, idx_end in find_text_list:
            for idx in range(idx_start, idx_end):
                index_dict[str(idx)] = True
        true_index_list = index_dict.keys()
        text_index = 0
        output_unicode_text = str()
        for char in unicode_text:
            if str(text_index) in true_index_list:
                output_unicode_text = '{0}{1}'.format(output_unicode_text, char)
            if char == ' ':
                output_unicode_text = '{0} '.format(output_unicode_text.strip())
            text_index += 1
        return output_unicode_text


#######
# def #
#######


########
# main #
########
if __name__ == '__main__':
    catch = CatchCalender()
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', action='store', dest='target_str', default=False, type=str, help='one string')
    parser.add_argument('-d', action='store', dest='dir_path', default=False, type=str, help='directory path')
    parser.add_argument('-f', action='store', dest='file_path', default=False, type=str, help='file path')
    parser.add_argument('-e', action='store', dest='encode_type', default='utf-8', type=str, help='encode set')
    arguments = parser.parse_args()
    count = 0
    if arguments.target_str:
        print(catch.catch_calender_text(arguments.target_str))
