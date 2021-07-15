#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""program"""
__author__ = "MINDsLAB"
__date__ = "creation: 2021-06-14, modification: 0000-00-00"

##########
# import #
##########
import os
import json
import time
import traceback
from datetime import datetime
from collections import OrderedDict
from cfg import config
from lib import logger, db_connection, util, catch_calender

###########
# options #
###########


#######
# def #
#######
def connect_db(log, db_type, db_conf):
    db = str()
    flag = True
    while flag:
        try:
            log.info('Try connecting to {0} DB ...'.format(db_type))
            if db_type.upper() == 'MYSQL':
                db = db_connection.MYSQL(db_conf)
                flag = False
            else:
                raise Exception('Not supported db ..(Oracle, MYSQL)')
            log.info('Success connect to {0} DB'.format(db_type))
        except Exception:
            err_str = traceback.format_exc()
            log.error(err_str)
            time.sleep(60)
    return db


def make_logger(req):
    contract_no = None
    if req.utter.meta.fields.get('contract_no') is not None:
        contract_no = str(req.utter.meta.fields['contract_no'].string_value)
    # Set logger
    now_dt = datetime.now()
    base_dir_path = '{0}/{1:0>2}{2:0>2}'.format(now_dt.year, now_dt.month, now_dt.day)
    log = logger.set_logger(
        logger_name='{0}_{1}'.format(config.DaConfig.logger_name, contract_no),
        log_dir_path=os.path.join(config.DaConfig.log_dir_path, base_dir_path),
        log_file_name='{0}.log'.format(contract_no),
        log_level=config.DaConfig.log_level
    )
    return log


def find_session_data(log, da_output_dict, req, target):
    data = None
    if da_output_dict.get(target) is not None:
        data = da_output_dict[target]
    if req.utter.meta.fields.get(target) is not None:
        temp_data = str(req.utter.meta.fields[target].string_value)
        data = temp_data if temp_data != 'None' else data
    if req.session.context.fields.get(target) is not None:
        temp_data = str(req.session.context.fields[target].string_value)
        data = temp_data if temp_data != 'None' else data
    log.debug('[Talk] {0} : {1}'.format(target, data))
    return data


def make_cust_data_class_dict(mysql_db, campaign_id):
    cust_data_class_list = util.select_cust_data_class(mysql_db, campaign_id)
    cust_data_class_dict = dict()
    for cust_data_class in cust_data_class_list:
        cust_data_class_dict[cust_data_class['COLUMN_KOR']] = str(cust_data_class['CUST_DATA_CLASS_ID'])
    return cust_data_class_dict


def after_sds_da(**kwargs):
    """
    This program that execute DA ( AFTER SDS )
    :param      kwargs:         Arguments
    :return:                    utter, da_output_dict, answer, sds_repeat
    """
    # 인자 setting
    req = kwargs.get('req')
    answer = kwargs.get('answer')
    da_output_dict = kwargs.get('da_output_dict')
    mysql_db = kwargs.get('db')
    res_content = kwargs.get('res_content')
    utter = kwargs.get('utter')
    # log setting
    log = make_logger(req)
    log.info('-----after_sds_da-----')
    # sds 재호출여부 설정
    sds_repeat = False
    # session_data or 이전 DA 데이터 불러오는 영역
    pre_intent = find_session_data(log, da_output_dict, req, 'pre_intent')
    contract_no = find_session_data(log, da_output_dict, req, 'contract_no')
    doing_tts = find_session_data(log, da_output_dict, req, 'doing_tts')
    call_id = find_session_data(log, da_output_dict, req, 'call_id')
    simplebot_id = find_session_data(log, da_output_dict, req, 'simplebot_id')
    campaign_id = find_session_data(log, da_output_dict, req, 'campaign_id')
    checked_voicemail = find_session_data(log, da_output_dict, req, 'checked_voicemail')
    intent_repeat_cnt = find_session_data(log, da_output_dict, req, 'intent_repeat_cnt')
    src_info = find_session_data(log, da_output_dict, req, 'src_info')
    cust_nm = find_session_data(log, da_output_dict, req, 'cust_nm')
    log.debug('[Talk] utter : {0}'.format(utter))
    log.debug('[Talk] res_content : {0}'.format(res_content))
    log.debug('[Talk] answer : {0}'.format(answer))
    return_dict = da_output_dict
    dest_intent = str()
    intent = str()
    try:
        # res_content 정보 중 dest_intent 정보 session_data 저장
        if 'meta' in res_content:
            if 'intentRel' in res_content['meta']:
                if 'destIntent' in res_content['meta']['intentRel']:
                    return_dict['destIntent'] = res_content['meta']['intentRel']['destIntent']
                    dest_intent = res_content['meta']['intentRel']['destIntent']
        if contract_no is None:
            contract_no = '280'
            campaign_id = '1'
        # res_content 정보 중 intent 정보 조회.
        if 'setMemory' in res_content:
            intent = res_content['setMemory']['intent']['intent']
        if intent == '처음으로':
            # cust_id 조회
            cust_id = util.select_cust_id_in_cm_contract(db=mysql_db, contract_no=contract_no)
            result = util.select_cust_info(db=mysql_db, cust_id=cust_id)
            cust_nm = result['CUST_NM']
            return_dict['cust_nm'] = cust_nm
        if intent == '최대반복초과종결':
            return_dict['destIntent'] = intent
        if dest_intent == 'DB조회':
            # cust_id 조회
            cust_id = util.select_cust_id(db=mysql_db, contract_no=contract_no)
            cust_data_class_dict = make_cust_data_class_dict(mysql_db, campaign_id)
            result = util.select_cust_info(db=mysql_db, cust_id=cust_id)
            cust_data_dict = json.loads(result['CUST_DATA'])
            src_info = cust_data_dict[cust_data_class_dict['정보출처']]
            return_dict['src_info'] = src_info
            if cust_data_dict[cust_data_class_dict['시나리오코드']] == '01':
                utter = '일반동의'
                sds_repeat = True
            else:
                utter = '일반동의'
                sds_repeat = True
        # intent가 빈값인 경우 REPEAT
        if utter == "...":
            utter = '무응답'
            sds_repeat = True
        elif intent == '':
            utter = 'UNKNOWN'
            sds_repeat = True
        # 모든 INTENT 공통
        answer = answer.replace('{고객명}', str(cust_nm))
        answer = answer.replace('{정보출처}', str(src_info))
    except Exception:
        log.error(traceback.format_exc())
    if sds_repeat:
        log.info('SDS REPEAT: utter -> {0}'.format(utter))
    for handler in log.handlers:
        handler.close()
        log.removeHandler(handler)
    return utter, return_dict, answer, sds_repeat


def set_session_data(req, intent, session_data, da_output_dict):
    """
    Set session data
    :param      req:                    Req
    :param      intent:                 Intent
    :param      session_data:           Session Data
    :param      da_output_dict:         DA output Dictionary
    :return:                            Modify Session Data
    """
    log = make_logger(req)
    log.info('-----set_session_data-----')
    # destIntent 저장.
    if 'destIntent' in da_output_dict:
        log.info('destIntent: {0}'.format(da_output_dict['destIntent']))
        session_data['destIntent'] = da_output_dict['destIntent']
    if 'cust_nm' in da_output_dict:
        session_data['cust_nm'] = da_output_dict['cust_nm']
    if 'cust_react' in da_output_dict:
        session_data['cust_react'] = da_output_dict['cust_react']
    if 'src_info' in da_output_dict:
        session_data['src_info'] = da_output_dict['src_info']
    for handler in log.handlers:
        handler.close()
        log.removeHandler(handler)
    return session_data


def pre_sds_da(**kwargs):
    """
    This program that execute DA ( AFTER SDS )
    :param      kwargs:         Arguments
    :return:                    utter
    """
    # 인자 setting
    req = kwargs.get('req')
    utter = kwargs.get('utter')
    mysql_db = kwargs.get('db')
    # log setting
    log = make_logger(req)
    log.info('#'*100)
    log.info('#'*100)
    log.info('-----pre_sds_da-----')
    # session_data or 이전 DA 데이터 불러오는 영역
    pre_intent = find_session_data(log, dict(), req, 'pre_intent')
    contract_no = find_session_data(log, dict(), req, 'contract_no')
    doing_tts = find_session_data(log, dict(), req, 'doing_tts')
    call_id = find_session_data(log, dict(), req, 'call_id')
    simplebot_id = find_session_data(log, dict(), req, 'simplebot_id')
    campaign_id = find_session_data(log, dict(), req, 'campaign_id')
    checked_voicemail = find_session_data(log, dict(), req, 'checked_voicemail')
    intent_repeat_cnt = find_session_data(log, dict(), req, 'intent_repeat_cnt')
    log.debug('[Talk] utter : {0}'.format(utter))
    return_dict = dict()
    try:
        catch_object = catch_calender.CatchCalender()
        catch_text = catch_object.catch_calender_text(utter)
        log.info('catch text: {0}'.format(catch_text))
        if len(catch_text.strip()) > 0:
            utter = '일정수립'
            return_dict['cust_react'] = catch_text
    except Exception:
        log.error(traceback.format_exc())
    for handler in log.handlers:
        handler.close()
        log.removeHandler(handler)
    return utter, return_dict


def rec_stop_da(**kwargs):
    """
    REC Stop DA
    :param      kwargs:         Arguments
    :return:
    """
    # 인자 setting
    req = kwargs.get('req')
    mysql_db = kwargs.get('db')
    # log setting
    log = make_logger(req)
    log.info('-----rec_stop_da-----')
    try:
        # session_data load
        contract_no = find_session_data(log, dict(), req, 'contract_no')
        call_id = find_session_data(log, dict(), req, 'call_id')
        dest_intent = find_session_data(log, dict(), req, 'destIntent')
        cust_react = find_session_data(log, dict(), req, 'cust_react')
        campaign_id = find_session_data(log, dict(), req, 'campaign_id')
        # cust_id 조회
        cust_id = util.select_cust_id_in_cm_contract(db=mysql_db, contract_no=contract_no)
        # Call_Try_Count 1로 UPDATE
        call_try_count = 1
        # AI시나리오결과상세 INSERT
        task_seq_nm = dest_intent
        try:
            task_seq = config.DaConfig.task_seq_dict[task_seq_nm]
        except Exception:
            log.error('task_seq_nm: {0}'.format(task_seq_nm))
            log.error('list: {0}'.format(config.DaConfig.task_seq_dict))
            task_seq = 'F001'
        # AI시나리오결과코드
        success_cd = '02'
        success_nm = '실패'
        for temp_success_cd, temp_success_tuple in config.DaConfig.success_cd_dict.items():
            temp_success_nm, temp_task_seq_list = temp_success_tuple
            if task_seq in temp_task_seq_list:
                success_cd = temp_success_cd
                success_nm = temp_success_nm
        # AI통화결과코드 INSERT
        results = util.select_call_history(db=mysql_db, call_id=call_id)
        dial_result = results[0]['DIAL_RESULT']
        dial_result_detail = dial_result
        if dest_intent == '부재종결' or dial_result in ('480', '500'):
        # if dest_intent == '부재종결' or dial_result in ('480', ):
            dial_result_detail = '600'
        # 고객반응 INSERT
        # 파일명, 파일경로 생성.
        file_name = 'record_{0}_{1}_{2}'.format(call_id, contract_no, campaign_id)
        rec_file_name = '{0}.wav'.format(file_name)
        rec_path = config.DaConfig.json_dir_path
        # CM_CONTRACT UPDATE
        util.update_cm_contract(
            db=mysql_db,
            contract_no=contract_no,
            call_try_count=call_try_count,
            task_seq=task_seq,
            task_seq_nm=task_seq_nm,
            success_cd=success_cd,
            success_nm=success_nm,
            cust_react=cust_react,
            rec_file_nm=rec_file_name,
            rec_path=rec_path,
        )
        util.update_call_history(
            db=mysql_db,
            call_id=call_id,
            dial_result_detail=dial_result_detail
        )
        # json 파일 생성.
        json_data = OrderedDict()
        json_data['CALL_ID'] = call_id
        json_data['CONTRACT_NO'] = contract_no
        json_data['CUST_ID'] = cust_id
        json_data['CAMPAIGN_ID'] = campaign_id
        json_file_name = '{0}.json'.format(file_name)
        json_file_path = os.path.join(config.DaConfig.json_dir_path, json_file_name)
        with open(json_file_path, 'w') as json_file:
            json.dump(json_data, json_file, indent='\t')
    except Exception:
        log.error(traceback.format_exc())
    for handler in log.handlers:
        handler.close()
        log.removeHandler(handler)
