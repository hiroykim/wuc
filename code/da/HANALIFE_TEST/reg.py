#!/usr/bin/python
# -*- coding: utf-8 -*-

"""program"""
__author__ = "MINDsLAB"
__date__ = "creation: 0000-00-00, modification: 0000-00-00"

###########
# imports #
###########
import re
import sys
from datetime import datetime, timedelta
import pdb

###########
# options #
###########
reload(sys)
sys.setdefaultencoding('utf-8')


#############
# constants #
#############

#########
# class #
#########
class Util():
    def __init__(self):
        pass

    def convert_number(self, var):
        try:
            int(var)
            return str(var)
        except Exception:
            var = var.replace('1', '일').decode('utf-8')
            #        global convart_var
            hanCount = len(re.findall(u'[\u3130-\u318F\uAC00-\uD7A3]+', var))
            if hanCount >= 1:
                try:
                    convart_var = self.change_bu(var)
                    print('convart_var(1) : ' + convart_var)
                    hanCount = len(re.findall(u'[\u3130-\u318F\uAC00-\uD7A3]+', convart_var.decode('utf-8')))
                    if hanCount >= 1:
                        convart_var = convart_var
                        convart_var = self.change(convart_var)
                        print('convert_var(2) : ' + str(convart_var))
                    else:
                        print('1차의 한글 더이상 없음1')
                except:
                    convart_var = ''
            else:
                convart_var = var
                print('2차의 한글 더이상 없음2')
            return str(convart_var)

    def change_bu(self, input_var):
        input_var = input_var.decode('utf-8')
        replace_dict = dict()
        for i in ['한', '두', '세', '네', '다섯', '여섯', '일곱', '여덟', '아홉', '열', '열한', '열두']:
            replace_dict['{0}'.format(i)] = ['한 {0}'.format(i)]
            replace_dict['{0}'.format(i)] = ['한{0}'.format(i)]
        for key, value_list in replace_dict.items():
            for value in value_list:
                if value in input_var:
                    input_var = input_var.replace(value, key)
        b = {
            '한': '1',
            '두': '2',
            '세': '3',
            '네': '4',
            '다섯': '5',
            '여섯': '6',
            '일곱': '7',
            '여덟': '8',
            '아홉': '9',
            '열': '10',
            '열한': '11',
            '열두': '12',
            '열세': '13',
            '열네': '14',
            '열다섯': '15',
            '열여섯': '16',
            '열일곱': '17',
            '열여덟': '18',
            '열아홉': '19',
            '스물': '20',
            '스물한': '21',
            '스물두': '22',
            '스물세': '23',
            '스물네': '24'
        }
        text = ['스물네', '스물세', '스물두', '스물한', '스물', '열아홉', '열여덟', '열일곱', '열여섯', '열다섯', '열네', '열세', '열두', '열한', '열', '아홉',
                '여덟', '일곱', '여섯', '다섯', '네', '세', '두', '한']
        for t in text:
            if input_var.find(t.decode('utf-8')) >= 0:
                input_var = input_var.replace(t, b[t])
            else:
                pass
        input_var = input_var.encode('utf-8')
        return input_var

    def change(self, input_var):
        input_var = input_var.decode('utf-8')
        kortext = '영일이삼사오육칠팔구1'.decode('utf-8')
        korman = '만억조'.decode('utf-8')
        dic = {'시': 10, '십': 10, '백': 100, '천': 1000, '만': 10000, '억': 100000000, '조': 1000000000000}
        result = 0
        tmpResult = 0
        num = 0
        for i in range(0, len(input_var)):
            token = input_var[i]
            check = kortext.find(input_var[i])
            if check == -1:
                try:
                    if korman.find(token) == -1:
                        if num != 0:
                            tmpResult = tmpResult + num * dic[token.encode('utf-8')]
                        else:
                            tmpResult = tmpResult + 1 * dic[token.encode('utf-8')]

                    else:
                        print("else")
                        tmpResult = tmpResult + num
                        if tmpResult != 0:
                            result = result + tmpResult * dic[token.encode('utf-8')]
                        else:
                            result = result + 1 * dic[token.encode('utf-8')]
                        tmpResult = 0
                except Exception as e:
                    import traceback as tb;
                    tb.print_exc()
                    print(e)
                num = 0
            else:
                num = check
        return result + tmpResult + num


class Reg(object):
    """
    Regular expression
    """
    def __init__(self, util_obj=None):
        """
        Init
        :param util_obj:
        """
        self.util_obj = util_obj
        # self.year_reg = re.compile(r'(0|1|2|3|4|5|6|7|8|9|일|하나|둘|셋|삼|사|오|육|륙|칠|팔|구|공|넷|영|십|이){1,4}년'.decode('utf8'))
        # self.month_reg = re.compile(
        #     r'(0|1|2|3|4|5|6|7|8|9|10|11|12|일|하나|둘|셋|삼|사|오|육|륙|칠|팔|구|공|넷|영|십|이|시){1,2}월'.decode('utf8'))
        # self.day_reg = re.compile(r'(0|1|2|3|4|5|6|7|8|9|10|11|12|13|14|15|16|17|18|19|20|21|22|23|24|25|26|27|28|29|30|31|\
        #                                   일|하나|둘|셋|삼|사|오|육|륙|칠|팔|구|공|넷|영|십|이){1,4}일'.decode('utf8'))
        self.hour_reg = re.compile(r'(0|1|2|3|4|5|6|7|8|9|10|11|12|13|14|15|16|17|18|19|20|21|22|23|24|\
                                          일|한|두|둘|셋|세|삼|사|네|오|다섯|육|륙|여섯|칠|일곱|팔|여덟|구|아홉|공|넷|영|십|열|이){1,3}시'.decode('utf8'))
        # self.hour_ban_reg = re.compile(r'(0|1|2|3|4|5|6|7|8|9|10|11|12|13|14|15|16|17|18|19|20|21|22|23|24|\
        #                                           일|한|두|둘|셋|세|삼|사|네|오|다섯|육|륙|여섯|칠|일곱|팔|여덟|구|아홉|공|넷|영|십|열|이){1,3}시\w?(반)'.decode('utf8'))
        # self.minute_reg = re.compile(r'(0|1|2|3|4|5|6|7|8|9|일|하나|둘|셋|세|삼|사|오|육|륙|칠|팔|구|공|넷|영|십|이){1,3}분'.decode('utf8'))
        # self.manwon_reg = re.compile(r'(0|1|2|3|4|5|6|7|8|9|일|하나|둘|셋|삼|사|오|육|륙|칠|팔|구|공|넷|영|십|이|백|천|만|억|조|경|해){1,20}원'.decode('utf8'))
        self.day_week_reg = re.compile(r'(월|화|수|목|금|토|일)요일'.decode('utf8'))
        self.week_reg = re.compile(r'(이번|다음|다다음|차|금){1,3}주'.decode('utf8'))
        self.day = re.compile(r'(있다가|일단|있다|이따|오늘|내일|내일모레|모레|글피)'.decode('utf8'))
        # self.day_week = {'월': 0, '화': 1, '수': 2, '목': 3, '금': 4, '토': 5, '일': 6}
        # self.week_day = {0: '월', 1: '화', 2: '수', 3: '목', 4: '금', 5: '토', 6: '일'}
        self.noon_reg = re.compile(r'오전|오후|저녁|아침|퇴근|점심|밤'.decode('utf8'))
        self.hour_plus_reg = re.compile(r'(0|1|2|3|4|5|6|7|8|9|10|11|12|13|14|15|16|17|18|19|20|21|22|23|24|\
                                        일|한|두|둘|셋|세|삼|사|네|오|다섯|육|륙|여섯|칠|일곱|팔|여덟|구|아홉|공|넷|영|십|열|이){1,2}시간\w?(뒤|후)'.decode('utf8'))
        # self.minute_plus_reg = re.compile(r'(0|1|2|3|4|5|6|7|8|9|일|하나|둘|셋|세|삼|사|오|육|륙|칠|팔|구|공|넷|영|십|이){1,3}분\w?(뒤|후)'.decode('utf8'))
        self.day_plus_reg = re.compile(r'(하루|이틀|사흘|나흘|닷세|엿세|이레|여드레|나흐레|열흘|잠시|며칠|몇일){1,3}(뒤|후)'.decode('utf8'))
        # self.week_check_reg = re.compile(r'(휴일|주말)'.decode('utf8'))
        # self.call_end_reg = re.compile(r'(통화|전화){1,3}(종료|끝다|끊어|끊다|끊을|끝내|끊고)'.decode('utf8'))


    def test(self, text):
        """
        Get Day
        :param      text:       Text
        :return:
        """
        slots = {}
        text = text.replace(' ', '').decode('utf8')
        iter_result = list()
        iter_result = self.day.finditer(text)
        test_list = []
        # pdb.set_trace()
        for val in iter_result:
            start = val.start()
            end = val.end()
            test_list.append(text[start:end].encode('utf8'))
        return test_list

    def get_day(self, text):
        """
        Get Day
        :param      text:       Text
        :return:
        """
        slots = {}
        text = text.replace(' ', '').decode('utf8')
        text = text.replace('일곱시', '7시')
        text = text.replace('일일', '1일')
        iter_result = list()
        for flag in range(1, 13):
            if flag == 1:
                iter_result = self.month_reg.finditer(text)
            elif flag == 2:
                iter_result = self.day_reg.finditer(text)
            elif flag == 3:
                iter_result = self.hour_reg.finditer(text)
            elif flag == 4:
                iter_result = self.day_week_reg.finditer(text)
            elif flag == 5:
                iter_result = self.week_reg.finditer(text)
            elif flag == 6:
                iter_result = self.year_reg.finditer(text)
            elif flag == 7:
                iter_result = self.minute_reg.finditer(text)
            elif flag == 8:
                iter_result = self.noon_reg.finditer(text)
            elif flag == 9:
                iter_result = self.day.finditer(text)
            elif flag == 10:
                iter_result = self.hour_plus_reg.finditer(text)
            elif flag == 11:
                iter_result = self.minute_plus_reg.finditer(text)
            elif flag == 12:
                iter_result = self.day_plus_reg.finditer(text)
            for val in iter_result:
                print slots
                start = val.start()
                end = val.end()
                end = end-1 if flag in [1, 2, 3, 5, 6, 7, 12] else (end-2)
                if flag in [8, 9]:
                    end = val.end()
                if flag in [10]:
                    end = val.end() - 3
                slot = text[start:end].encode('utf8')
                # print 'flag: {0} target: {1}'.format(flag, slot)
                if flag in [1, 2, 3, 6, 7, 10]:
                    slot = self.util_obj.convert_number(slot)
                if flag == 1:
                    slots['month'] = slot
                elif flag == 2:
                    slots['day'] = slot
                elif flag == 3:
                    slots['hour'] = slot
                    # '시'를 두번 발화했을 시 앞의 '시'를 선택하기 위한 break 문
                    break
                elif flag == 4:
                    # slot = slot + "일"
                    slots['weekday'] = slot
                elif flag == 5:
                    slots['week'] = slot
                elif flag == 6:
                    slots['year'] = slot
                elif flag == 7:
                    slots['minute'] = slot
                elif flag == 8:
                    if slot in ['오전', '아침']:
                        slot = 'AM'
                    elif slot in ['오후', '저녁', '퇴근', '밤']:
                        slot = 'PM'
                    elif slot in ['점심']:
                        slot = 'ATNOON'
                    slots['noon'] = slot
                elif flag == 9:
                    slots['weekday'] = slot
                elif flag == 10:
                    slots['hour_plus'] = slot
                elif flag == 11:
                    slots['minute_plus'] = slot
                elif flag == 12:
                    slots['day_plus'] = slot
        # # 다음주라는 발화인 경우
        if ['week'] == slots.keys():
            new_time = datetime.now() + timedelta(days=7)
            slots['minute'] = new_time.minute
            slots['hour'] = new_time.hour
            slots['day'] = new_time.day
            slots['month'] = new_time.month
            slots['year'] = new_time.year
        if 'weekday' in slots.keys() and 'week' in slots.keys():
            slots.update(self.cal_day(slots['weekday'], slots['week']))
            del slots['weekday']
            del slots['week']
        elif 'weekday' in slots.keys():
            slots.update(self.cal_day(slots['weekday']))
            del slots['weekday']
           
        if 'hour_plus' in slots.keys():
            new_time = (datetime.now() + timedelta(hours=int(slots['hour'])))
            slots['hour'] = new_time.hour
            print 'hour_plus ::: {0}'.format(new_time)
            slots['minute'] = new_time.minute
            if datetime.now().day != new_time.day:
                slots['day'] = new_time.day
            if datetime.now().month != new_time.month:
                slots['month'] = new_time.month
            if datetime.now().year != new_time.year:
                slots['year'] = new_time.year
        if 'minute_plus' in slots.keys():
            new_time = (datetime.now() + timedelta(minutes=int(slots['minute'])))
            slots['minute'] = new_time.minute
            if datetime.now().hour != new_time.hour:
                slots['hour'] = new_time.hour
            if datetime.now().day != new_time.day:
                slots['day'] = new_time.day
            if datetime.now().month != new_time.month:
                slots['month'] = new_time.month
            if datetime.now().year != new_time.year:
                slots['year'] = new_time.year
        if 'day_plus' in slots.keys():
            slots['day'] = '0'
            print slots
        now = datetime.now()
        # 정규식이 하나라도 탐지됐을 경우에만 default값 삽입
        if len(slots.keys()) > 0:
            if 'year' not in slots.keys():
                slots['year'] = now.year
            if 'day' not in slots.keys():
                slots['day'] = '0'  # 일자 발화없을 경우
            if 'month' not in slots.keys():
                slots['month'] = now.month
                if int(slots['day']) != 0:
                    if int(slots['day']) < int(now.day):
                        slots['month'] = now.month + 1
            if 'hour' not in slots.keys() and 'noon' in slots.keys():
                if slots['noon'] == 'AM':    # 시간발화 없이, 오전/오후 등의 발화만 존재할 경우, 자동으로 시간 저장되는 부분을 0으로 만들기 위함
                    slots['hour'] = '0'
                elif slots['noon'] == 'PM':
                    slots['hour'] = '0'
                elif slots['noon'] == 'ATNOON':
                    slots['hour'] = '0'
                    slots['noon'] = 'PM'
            if 'hour' not in slots.keys():
                slots['hour'] = '0'     # 시간 발화없을 경우
            if 'hour' in slots.keys() and 'noon' not in slots.keys():
                hour = int(slots['hour'])
                slots['noon'] = 'AM' if 8 <= hour < 12 else 'PM'
            if 'minute' not in slots.keys():
                slots['minute'] = 0
            # 요일 삽입
            if 'week_day' not in slots and slots['day'] != '0':
                target_date = datetime(int(slots['year']), int(slots['month']), int(slots['day']))
                slots['week_day'] = self.week_day[target_date.weekday()]
            # 지금 시간과 비교
            hour = int(slots['hour'])
            if slots['noon'] == 'PM' and hour < 12:
                hour += 12
            if slots['noon'] == 'PM' and int(slots['hour']) > 12:
                slots['hour'] = str(int(slots['hour']) - 12)
            print("!@#$%slots :: {}".format(slots))
            print 'slots: {0}'.format(slots)
            print 'value: {0}'.format(now)
            # 날짜가 없을 경우, 오늘 날짜를 default로
            if slots['day'] == '0':
                slots['day'] = datetime.now().stftime('%d')
                slots['week_day'] = self.week_day[datetime.now().weekday()]
            if slots['day'] != '0':
                print 'bool : {0}'.format(datetime(int(slots['year']), int(slots['month']), int(slots['day']), hour))
                if now > datetime(int(slots['year']), int(slots['month']), int(slots['day']), hour, int(slots['minute'])) and int(slots['hour']) != 0:
                    slots = dict()
        return slots

    def cal_day(self, weekday, week='이번'):
        """
        Calculate Date
        :param      weekday:        Week day
        :param      week:           Week Count
        :return:                    day Dictionary
        """

        def get_day(time):
            """
            Get Day
            :param      time:       Time
            :return:                Year, Month, Day
            """
            return time.year, time.month, time.day

        def get_target_day(temp_compare_day, mul):
            """
            Get Target Day
            :param      temp_compare_day:        Compare Day
            :param      mul:                Week Count
            :return:
            """
            temp_week = 7 * mul
            if temp_compare_day < 0 or temp_compare_day > 0:
                temp_target_day = temp_week + temp_compare_day
            else:
                temp_target_day = temp_week
            return temp_target_day

        now = datetime.now()
        now_weekday = now.weekday()
        if weekday in self.day_week:
            target_day = self.day_week[weekday]
        else:
            #if weekday in ['오늘', '이따', '있다', '있다가', '일단']:
            if weekday in ['오늘']:
                target_day = now_weekday
            elif weekday == '내일':
                target_day = now_weekday + 1
            elif weekday == '내일모레' or weekday == '모레':
                target_day = now_weekday + 2
            elif weekday == '글피':
                target_day = now_weekday + 3
            if target_day >= 7:
                target_day = target_day - 7
        if week == '이번' or week == '금':
            if now_weekday < target_day:
                temp_target_day = target_day - now_weekday
                target_now = now + timedelta(days=temp_target_day)
                result = get_day(target_now)
            elif now_weekday > target_day:
                temp_target_day = 7 + (target_day - now_weekday)
                target_now = now + timedelta(days=temp_target_day)
                result = get_day(target_now)
            elif now_weekday == target_day:
                #temp_target_day = 7 if weekday not in ['오늘', '이따', '있다', '있다가', '일단'] else 0
                temp_target_day = 0
                target_now = now + timedelta(days=temp_target_day)
                result = get_day(target_now)
        elif week == '다음' or week == '차':
            print 'target_day: {0}'.format(target_day)
            print 'now_weekday: {0}'.format(now_weekday)
            compare_day = target_day - now_weekday
            temp_target_day = get_target_day(compare_day, 1)
            target_now = now + timedelta(days=temp_target_day)
            result = get_day(target_now)
        elif week == '다다음':
            compare_day = target_day - now_weekday
            temp_target_day = get_target_day(compare_day, 2)
            target_now = now + timedelta(days=temp_target_day)
            result = get_day(target_now)
        else:
            return -1
        dic = {'year': result[0], 'month': result[1], 'day': result[2], 'week_day': self.week_day[target_day]}
        print "--" * 100
        print dic
        print "--" * 100
        return dic

    def get_money(self, utter):
        """
        Get Money
        :param      text:       Text
        :return:
        """
        slots = dict()
        try:
            # print self.util_obj.change(text)
            text = utter.replace(' ', '').decode('utf8')
            iter_result = self.manwon_reg.finditer(text)
            print iter_result
            for val in iter_result:
                start = val.start()
                end = val.end()
                end = end - 1
                slot = text[start:end].encode('utf8')
                slot = self.util_obj.convert_number(slot)
                slots['manwon'] = slot
        except Exception:
            pass
        return slots

    def get_pay_day(self, text):
        """
        Get Pay day
        :param      text:       Text
        :return:
        """
        slots = dict()
        try:
            # print self.util_obj.change(text)
            text = text.replace(' ', '').decode('utf8')
            iter_result = self.day_reg.finditer(text)
            print iter_result
            for val in iter_result:
                start = val.start()
                end = val.end()
                end = end - 1
                slot = text[start:end].encode('utf8')
                slot = self.util_obj.convert_number(slot)
                slots['pay_day'] = slot
        except Exception:
            pass
        return slots

    def get_week_check(self, text):
        """
        get_week_check    주말, 휴일 등
        :param      text:       Text
        :return:
        """
        slots = dict()
        try:
            # print self.util_obj.change(text)
            text = text.replace(' ', '').decode('utf8')
            iter_result = self.week_check_reg.finditer(text)
            print iter_result
            for val in iter_result:
                start = val.start()
                end = val.end()
                slot = text[start:end].encode('utf8')
                slots['week_check'] = slot
        except Exception:
            pass
        return slots

    def get_call_end(self, text):
        """
        get_call_end    전화 끊으려할 때 등
        :param      text:       Text
        :return:
        """
        slots = dict()
        try:
            # print self.util_obj.change(text)
            text = text.replace(' ', '').decode('utf8')
            iter_result = self.call_end_reg.finditer(text)
            print iter_result
            for val in iter_result:
                start = val.start()
                end = val.end()
                slot = text[start:end].encode('utf8')
                slots['call_end'] = slot
        except Exception:
            pass
        return slots


if __name__ == '__main__':
    service = Util()
    reg = Reg(service)
    result = reg.get_day('구십구년 오월 이일이요')
    # result = reg.get_week_check('주말에요')
    #result = reg.get_call_end('31일 4시 쯤이요')
    # result = reg.get_money('구십팔만원')
    # result = reg.get_pay_day('이십오일')
    print result
