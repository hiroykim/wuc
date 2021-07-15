#!/usr/bin/python
# -*- coding: utf-8 -*-

"""program"""
__author__ = "MINDsLAB"
__date__ = "creation: 2020-08-11, modification: 0000-00-00"

###########
# imports #
###########
import os
import re
import argparse
import traceback


#########
# class #
#########
class ChangeArabic(object):
    def __init__(self):
        self.except_word = [
            u'구요', u'금천구', u'기억이', u'공공기관', u'부천', u'불만이', u'7일', u'30일', u'90일', u'이동장치', u'심사',
            u'만일', u'새천년', u'시경', u'시구', u'시일', u'영호', u'오동나무', u'천일염', u'천천이', u'대학교', u'며칠',
            u'페이백', u'내일', u'어린이', u'청구', u'사회기능'
        ]
        self.unit_dict = {
            1: ['원', '개', '년', '월', '일', '분', '동', '호', '종', '병', '회', '길', '대', '층', '%'],
            2: ['개월', '프로', '번지', '단지', '번길', '키로', '주일'],
            3: ['퍼센트', '퍼센터', '퍼센투', '퍼센토']
        }
        self.replace_dict = {
            '이십니까': ' 이 십 니까',
            '나오시는': '나오 시는',
            '이다': ' 이다',
            ' 일이 ': ' 일 이 ',
            '이상': ' 이상',
            '이동시': '이 동시',
            '만십오세': '만 십오세',
            '만십팔세': '만 십오세',
            '만이십세': '만 이십세',
            '만육십오세': '만 십오세',
            '이었습니다': ' 이었습니다',
            '이시고': ' 이시고',
        }
        unit_str_list = list()
        for key, value_list in self.unit_dict.items():
            for value in value_list:
                unit_str_list.append(value)
        unit_str = '|'.join(unit_str_list)
        self.number_unit_re = re.compile(
            (r'(일|이|삼|사|오|육|칠|팔|구|영|십|백|천|만|억|하나|둘){1,}'
            + '({0})'.format(unit_str)))
        self.number_re = re.compile(
            r'(일|이|삼|사|오|육|칠|팔|구|영|십|백|천|만|억|하나|둘){3,}')
        self.number_check_re = re.compile(
            r'(일|이|삼|사|오|육|칠|팔|구|영|십|백|천|만|억|하나|둘){2,}')

    @staticmethod
    def replace_arabic(unicode_text, replace_list):
        """
        Replace Arabic
        :param         unicode_text:         Target Text
        :param         replace_list:         Replace List
        :return:                             Output Text
        """
        replace_list.reverse()
        for idx_start, idx_end, arabic in replace_list:
            if len(arabic) > 0:
                if unicode_text[idx_end:idx_end+1] == u'원':
                    try:
                        unicode_text = u'{0}{1}{2}'.format(
                            unicode_text[:idx_start], format(int(arabic), ",d"), unicode_text[idx_end:])
                    except Exception:
                        idx = int()
                        for idx in range(len(arabic)):
                            try:
                                u'{0}{1}{2}{3}'.format(
                                    unicode_text[:idx_start], arabic[:idx], format(int(arabic[idx:]), ",d"),
                                    unicode_text[idx_end:])
                                break
                            except Exception:
                                continue
                        unicode_text = u'{0}{1}{2}{3}'.format(
                            unicode_text[:idx_start], arabic[:idx], format(int(arabic[idx:]), ",d"),
                            unicode_text[idx_end:])
                else:
                    unicode_text = u'{0}{1}{2}'.format(unicode_text[:idx_start], arabic, unicode_text[idx_end:])
        return unicode_text

    @staticmethod
    def change_arabic(target_txt):
        """
        Change Arabic
        :param         target_txt:         Target Text
        :return:                           Arabic Text
        """
        replace_dict = {
            '하나': '일', '둘': '이', '셋': '삼', '넷': '사', '다섯': '오', '여섯': '육', '일곱': '칠', '여덟': '팔',
            '아홉': '구', '열': '십', '스물': '이십', '서른': '삼십', '마흔': '사십'
        }
        number_dict = {
            '일': '1', '이': '2', '삼': '3', '사': '4', '오': '5',
            '육': '6', '유': '6', '칠': '7', '팔': '8', '구': '9', '영': '0', '공': '0'
        }
        size_dict = {'시': '10', '십': '10', '백': '100', '천': '1000', '만': '10000', '억': '100000000'}
        for before, after in replace_dict.items():
            target_txt = target_txt.replace(before, after)
        arabic_txt = str()
        count_type = str()
        current_size = 1
        current_unit_size = 1
        for idx in range(len(target_txt)-1, -1, -1):
            value = target_txt[idx]
            if value in number_dict.keys():
                if count_type == 'size_size':
                    arabic_txt = int(number_dict[value]) * current_unit_size * current_size + (
                                int(arabic_txt) % (current_unit_size * current_size))
                    count_type = 'size_number'
                elif count_type == 'size_number':
                    arabic_txt = target_txt[:idx+1] + str(arabic_txt)
                    break
                else:
                    count_type = 'number'
                    arabic_txt = number_dict[value] + arabic_txt
            elif value in size_dict.keys():
                if value in ['만', '억']:
                    if int(size_dict[value]) > current_unit_size:
                        current_unit_size = int(size_dict[value])
                    else:
                        break
                    current_size = 1
                if count_type in ['size_size', 'size_number'] and value in ['십', '백', '천']:
                    current_value = 0 if int(arabic_txt) / current_unit_size == 1 else int(
                        arabic_txt) / current_unit_size
                    current_value = int(current_value)
                    arabic_txt = (int(size_dict[value]) + current_value) * current_unit_size + (
                                int(arabic_txt) % current_unit_size)
                    if value in ['십', '백', '천']:
                        current_size = int(size_dict[value])
                    count_type = 'size_size'
                elif count_type == 'number' and len(arabic_txt) <= 1 or count_type in ['size_number', 'size_size']:
                    count_type = 'size_size'
                    arabic_txt = str(int(size_dict[value]) + int(arabic_txt))
                    if value in ['십', '백', '천']:
                        current_size = int(size_dict[value])
                elif count_type == 'number':
                    arabic_txt = target_txt[:idx+1] + str(arabic_txt)
                    break
                elif len(count_type) == 0:
                    arabic_txt = str(int(size_dict[value]))
                    count_type = 'size_size'
                    if value in ['십', '백', '천']:
                        current_size = int(size_dict[value])
                else:
                    break
        return str(arabic_txt)

    def change_arabic_text(self, text):
        """
        change Arabic text
        :param         text:         Target Text
        :return:                     Output Text
        """
        for key, value in self.replace_dict.items():
            text = text.replace(key, value)
        unicode_text = text
        replace_list = list()
        # unit change
        iter_result = self.number_unit_re.finditer(unicode_text)
        for value in iter_result:
            idx_start = value.start()
            idx_end = value.end()
            temp_idx_end = idx_end
            flag = False
            for unit_len in range(3, 0, -1):
                unit_list = self.unit_dict[unit_len]
                for unit in unit_list:
                    if unit in unicode_text[idx_start:idx_end]:
                        if unit == '일':
                            result = self.number_check_re.finditer(unicode_text[idx_end:])
                            for temp_value in result:
                                if temp_value.start() == 0:
                                    flag = True
                                break
                        temp_idx_end = idx_end - unit_len
                        break
                if idx_end != temp_idx_end:
                    idx_end = temp_idx_end
                    break
            if flag:
                continue
            except_flag = False
            for target_word in self.except_word:
                start = 0 if idx_start - 2 < 0 else idx_start - 2
                if target_word in unicode_text[start:idx_end + 3]:
                    except_flag = True
            if not except_flag:
                arabic = self.change_arabic(unicode_text[idx_start:idx_end])
                replace_list.append((idx_start, idx_end, arabic))
        unicode_text = self.replace_arabic(unicode_text, replace_list)
        # number check change
        # replace_list = list()
        # iter_result = self.number_check_re.finditer(unicode_text)
        # for value in iter_result:
        #     idx_start = value.start()
        #     idx_end = value.end()
        #     temp_idx_end = idx_end
        #     flag = False
        #     for unit_len in range(3, 0, -1):
        #         unit_list = self.unit_dict[unit_len]
        #         for unit in unit_list:
        #             if unit in unicode_text[idx_start:idx_end]:
        #                 if unit == '일':
        #                     result = self.number_check_re.finditer(unicode_text[idx_end:])
        #                     for temp_value in result:
        #                         if temp_value.start() == 0:
        #                             flag = True
        #                         break
        #                 temp_idx_end = idx_end - unit_len
        #                 break
        #         if idx_end != temp_idx_end:
        #             idx_end = temp_idx_end
        #             break
        #     if flag:
        #         continue
        #     except_flag = False
        #     for target_word in self.except_word:
        #         start = 0 if idx_start - 2 < 0 else idx_start - 2
        #         if target_word in unicode_text[start:idx_end + 3]:
        #             except_flag = True
        #     if not except_flag:
        #         arabic = self.change_arabic(unicode_text[idx_start:idx_end])
        #         replace_list.append((idx_start, idx_end, arabic))
        # unicode_text = self.replace_arabic(unicode_text, replace_list)
        # number change
        # replace_list = list()
        # iter_result = self.number_re.finditer(unicode_text)
        # for value in iter_result:
        #     idx_start = value.start()
        #     idx_end = value.end()
        #     except_flag = False
        #     for target_word in self.except_word:
        #         start = 0 if idx_start - 2 < 0 else idx_start - 2
        #         if target_word in unicode_text[start:idx_end + 3]:
        #             except_flag = True
        #     if not except_flag:
        #         arabic = self.change_arabic(unicode_text[idx_start:idx_end])
        #         replace_list.append((idx_start, idx_end, arabic))
        # unicode_text = self.replace_arabic(unicode_text, replace_list)
        text = unicode_text
        for key, value in self.replace_dict.items():
            text = text.replace(value, key)
        return text


########
# main #
########
if __name__ == '__main__':
    change = ChangeArabic()
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', action='store', dest='target_str', default=False, type=str, help='one string')
    parser.add_argument('-d', action='store', dest='dir_path', default=False, type=str, help='directory path')
    parser.add_argument('-f', action='store', dest='file_path', default=False, type=str, help='file path')
    arguments = parser.parse_args()
    count = 0
    if arguments.target_str:
        print(change.change_arabic_text(arguments.target_str))
    elif arguments.dir_path:
        w_ob = os.walk(arguments.dir_path)
        for dir_path, sub_dirs, files in w_ob:
            for file_name in files:
                if file_name.endswith('_arabic.txt'):
                    continue
                output_file_path = os.path.join(dir_path, '{0}_arabic.txt'.format(os.path.splitext(file_name)[0]))
                if os.path.exists(output_file_path):
                    os.remove(output_file_path)
                output_file = open(output_file_path, 'w')
                target_file_path = os.path.join(dir_path, file_name)
                target_file = open(target_file_path)
                for line in target_file:
                    try:
                        print(change.change_arabic_text(line.strip()), file=output_file)
                    except Exception:
                        pass
                target_file.close()
                output_file.close()
                count += 1
                print('processing.. {0}'.format(count))
    elif arguments.file_path:
        target_file = open(arguments.file_path)
        for line in target_file:
            print(change.change_arabic_text(line))
        target_file.close()
