#!/usr/bin/python
# -*- coding: utf-8 -*-

"""program"""
__author__ = "MINDsLAB"
__date__ = "creation: 2021-06-16, modification: 0000-00-00"

###########
# imports #
###########
import collections
import os
import sys
import json
import time
import socket
import signal
import shutil
import requests
import traceback
import subprocess
from datetime import datetime, timedelta
from cfg import config
from lib import logger, util, db_connection, cipher

###########
# options #
###########
reload(sys)
sys.setdefaultencoding("utf-8")


#########
# class #
#########
class DAPOSTDaemon(object):
    def __init__(self):
        self.conf = config.DAPOSTConfig
        self.logger = logger.get_timed_rotating_logger(
            logger_name=self.conf.logger_name,
            log_dir_path=self.conf.log_dir_path,
            log_file_name=self.conf.log_file_name,
            backup_count=self.conf.backup_count,
            log_level=self.conf.log_level
        )
        self.host_name = socket.gethostname()
        self.mssql_db = self.connect_db('MSSQL', config.MSConfig)
        self.mysql_db = self.connect_db('MYSQL', config.MYConfig)
        self.cipher_object = cipher.AESCipher(config.AESConfig)

    def set_sig_handler(self):
        signal.signal(signal.SIGTSTP, signal.SIG_IGN)
        signal.signal(signal.SIGTTOU, signal.SIG_IGN)
        signal.signal(signal.SIGTTIN, signal.SIG_IGN)
        signal.signal(signal.SIGHUP, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, sig, frame):
        if frame:
            pass
        if sig == signal.SIGHUP:
            return
        if sig == signal.SIGTERM or sig == signal.SIGINT:
            if self.mssql_db:
                self.mssql_db.conn.commit()
            self.logger.info('stopped by interrupt')
            sys.exit(0)

    def connect_db(self, db_type, db_conf):
        db = ''
        flag = True
        while flag:
            try:
                self.logger.info('Try connecting to {0} DB ...'.format(db_type))
                if db_type.upper() == 'MSSQL':
                    db = db_connection.MSSQL(db_conf)
                    flag = False
                elif db_type.upper() == 'MYSQL':
                    db = db_connection.MYSQL(db_conf)
                    flag = False
                else:
                    raise Exception('Not supported db ..(Oracle, MSSQL, MYSQL)')
                self.logger.info('Success connect to {0} DB'.format(db_type))
            except Exception:
                err_str = traceback.format_exc()
                self.logger.error(err_str)
                time.sleep(60)
        return db

    def conv_rec_file(self, rec_info):
        rec_id = rec_info['REC_ID']
        rec_pth = rec_info['REC_PTH']
        rec_file_nm = rec_info['REC_FILE_NM']
        self.logger.info('\t 3) Convert record wav to mp3')
        if not os.path.exists(os.path.join(rec_pth, rec_file_nm)):
            self.logger.error("Can't find record file [REC_PTH= {0}, REC_FILE_NM= {1}]".format(rec_pth, rec_file_nm))
            return False

    def check_json_file(self, json_file_path):
        try:
            self.logger.info('\t 1) Check Json file')
            json_file = open(json_file_path)
            json_data = json.load(json_file)
            json_dict = dict(json_data)
            json_file.close()
            for param, value in json_dict.items():
                if not value:
                    raise Exception("{0} is wrong data. Check Json file".format(param))
        except Exception:
            self.logger.error(traceback.format_exc())
            return False
        return json_dict

    def polling_directory(self):
        """
        0. Polling directory
        :return:        Sorted Json File Path List
        """
        self.logger.debug('0. Polling directory [{0}]...'.format(self.conf.polling_dir_path))
        json_file_path_list = list()
        w_ob = os.walk(self.conf.polling_dir_path)
        for dir_path, sub_dirs, files in w_ob:
            for file_name in files:
                if file_name.endswith('.json'):
                    json_file_path_list.append(os.path.join(dir_path, file_name))
        sorted_json_file_path_list = sorted(json_file_path_list, key=os.path.getmtime, reverse=False)
        return sorted_json_file_path_list

    def error_encrypt(self, target_file_path, error_dir_path):
        if not os.path.exists(target_file_path):
            self.logger.error('target file is not exists -> {0}'.format(target_file_path))
        self.logger.error('target file move {0} -> {1}'.format(target_file_path, error_dir_path))
        if not os.path.exists(error_dir_path):
            os.makedirs(error_dir_path)
        shutil.copy(target_file_path, error_dir_path)
        file_name = os.path.basename(target_file_path)
        error_file_path = os.path.join(error_dir_path, file_name)
        self.logger.error('encrypt file: {0}'.format(error_file_path))
        self.cipher_object.encrypt_file(error_file_path)
        if os.path.exists('{0}.enc'.format(error_file_path)) and os.path.exists(target_file_path):
            if target_file_path.endswith('.wav'):
                pass
            else:
                os.remove(target_file_path)
            os.remove(error_file_path)

    def error_process(self, process_step=str(), target_dict=dict()):
        """
        Error Process
        :param      process_step:           Process_step
        :param      target_dict:            Target Dictionary
        :return:
        """
        self.logger.error('Error Process (process step: {0})'.format(process_step))
        if process_step in ('1', '2'):
            json_file_path = target_dict['json_file_path']
            rec_path = target_dict['CM_CONTRACT']['REC_PTH']
            rec_file_nm = target_dict['CM_CONTRACT']['REC_FILE_NM']
            rec_file_path = os.path.join(rec_path, rec_file_nm)
            error_dir_path = self.conf.err_json_dir_path if process_step == '1' else self.conf.err_json_dir_path
            self.error_encrypt(rec_file_path, error_dir_path)
            if not os.path.exists(json_file_path):
                self.logger.error('json file is not exists -> {0}'.format(json_file_path))
            self.error_encrypt(json_file_path, error_dir_path)
        if process_step in ('3', '4'):
            json_file_path = target_dict['json_file_path']
            rec_path = target_dict['CM_CONTRACT']['REC_PTH']
            rec_file_nm = target_dict['CM_CONTRACT']['REC_FILE_NM']
            rec_file_path = os.path.join(rec_path, rec_file_nm)
            error_dir_path = self.conf.err_metis_dir_path
            self.error_encrypt(json_file_path, error_dir_path)
            self.error_encrypt(rec_file_path, error_dir_path)
        if process_step in ('5', '6'):
            json_file_path = target_dict['json_file_path']
            error_dir_path = self.conf.err_tran_dir_path
            rec_path = target_dict['CM_CONTRACT']['REC_PTH']
            rec_file_nm = target_dict['CM_CONTRACT']['REC_FILE_NM']
            rec_file_path = os.path.join(rec_path, rec_file_nm)
            self.error_encrypt(json_file_path, error_dir_path)
            self.error_encrypt(rec_file_path, error_dir_path)
            util.update_cm_contract_rec_tran(
                db=self.mysql_db,
                contract_no=target_dict['json_data']['CONTRACT_NO'],
                rec_tran_yn='N'
            )

    def json_check(self, json_file_path):
        """
        1. Json Check
        :param      json_file_path:         Json File Path
        :return:                            Check Json File Dictionary
        """
        self.logger.info('1. Json Data Check')
        try:
            json_dict = self.check_json_file(json_file_path)
            """
            Json {
                'CUST_ID': '', 'CONTRACT_NO': '', 'CALL_ID': '', 'CAMPAIGN_ID': ''
            }
            """
            if not json_dict:
                raise Exception('json file is empty: {0}'.format(json_file_path))
            target_dict = {
                'json_file_path': json_file_path,
                'json_data': json_dict
            }
        except Exception:
            raise Exception(traceback.format_exc())
        return target_dict

    def rec_file_check(self, target_dict):
        """
        2. Rec File Check
        :param      target_dict:        Target Dictionary
        :return:                        Modify Target Dictionary
        """
        self.logger.info('2. Rec File Check')
        try:
            rec_info = util.select_rec_info(db=self.mysql_db, contract_no=target_dict['json_data']['CONTRACT_NO'])
            if not rec_info:
                raise Exception()
            rec_file_path = os.path.join(rec_info['REC_PTH'], rec_info['REC_FILE_NM'])
            if not os.path.exists(rec_file_path):
                self.logger.error('file is not exists: {0}'.format(rec_file_path))
                raise Exception(traceback.format_exc())
            target_dict['CM_CONTRACT'] = rec_info
        except Exception:
            raise Exception(traceback.format_exc())
        return target_dict

    def make_cust_data_class_dict(self, mysql_db, campaign_id):
        cust_data_class_list = util.select_cust_data_class(mysql_db, campaign_id)
        cust_data_class_dict = dict()
        for cust_data_class in cust_data_class_list:
            cust_data_class_dict[cust_data_class['COLUMN_KOR'].encode('utf-8')] = str(cust_data_class['CUST_DATA_CLASS_ID'])
        return cust_data_class_dict

    def requests_metis(self, target_dict):
        """
        3. Requests METIS
        :param      target_dict:        Target Dictionary
        :return:                        Modify Target Dictionary
        """
        self.logger.info('3. Requests METIS')
        try:
            json_data = target_dict['json_data']
            cust_info_data = util.select_cust_info(db=self.mysql_db, cust_id=json_data['CUST_ID'])
            if not cust_info_data:
                raise Exception()
            target_dict['CUST_INFO'] = cust_info_data
            call_history_data = util.select_call_history(db=self.mysql_db, call_id=json_data['CALL_ID'])
            if not call_history_data:
                raise Exception()
            target_dict['CALL_HISTORY'] = call_history_data[0]
            cust_data_class_dict = self.make_cust_data_class_dict(self.mysql_db, json_data['CAMPAIGN_ID'])
            cust_data = json.loads(target_dict['CUST_INFO']['CUST_DATA'])
            file_type = 'I' if target_dict['CM_CONTRACT']['IS_INBOUND'] == 'Y' else 'O'
            start_time = target_dict['CALL_HISTORY']['START_TIME']
            target_dict['CM_CONTRACT']['REC_CONV_FILE_NM'] = '{0}0000_{1}_{2}_{3}_A.mp3'.format(
                start_time,
                target_dict['CALL_HISTORY']['SIP_USER'],
                file_type,
                cust_data[cust_data_class_dict['상담사ID']]
            )
            post_data = {
                'cnsCusId': cust_data[cust_data_class_dict['상담고객ID']],  # 상담고객ID
                'aiSnroRslCd': target_dict['CM_CONTRACT']['SUCCESS_CD'],    # AI시나리오결과코드
                'aiSnroRslDtl': target_dict['CM_CONTRACT']['TASK_SEQ'],     # AI시나리오결과상세
                'aiTcRslCd': target_dict['CALL_HISTORY']['DIAL_RESULT_DETAIL'],        # AI통화결과코드
                'cusRact': target_dict['CM_CONTRACT']['CUST_REACT'],          # 고객반응
                'tcHr': str(int(float(target_dict['CALL_HISTORY']['DURATION']))),             # 통화시간 (초단위)
                'tcStTm': start_time,           # 통화시작시간 (YYYYMMDDHH24MISS)
                'tcEdTm': target_dict['CALL_HISTORY']['END_TIME'],                  # 통화종료시간 (YYYYMMDDHH24MISS)
                'fileNm': os.path.splitext(target_dict['CM_CONTRACT']['REC_CONV_FILE_NM'])[0],           # 녹취파일명
            }
            cus_cns_resp_id = str()
            try:
                result = requests.post(config.MetisConfig.host, data=post_data)
                self.logger.info('\turl: {0}'.format(config.MetisConfig.host))
                self.logger.info('\tparameter: {0}'.format(post_data))
                self.logger.info('\tresult: {0}'.format(result.text))
                cus_cns_resp_id = result.text
                if cus_cns_resp_id == '-1':
                    raise Exception('metis return data is -1')
            except Exception:
                self.logger.error(traceback.format_exc())
                self.logger.error(config.MetisConfig.host)
                self.logger.error(post_data)
                raise Exception()
            if not cus_cns_resp_id:
                raise Exception()
            target_dict['CM_CONTRACT']['REC_ID'] = cus_cns_resp_id
            sub_dir_name = '{0}/{1}'.format(start_time[:8], start_time[8:10])
            rec_conv_pth = os.path.join(self.conf.rec_conv_path, sub_dir_name)
            if not os.path.exists(rec_conv_pth):
                os.makedirs(rec_conv_pth)
            target_dict['CM_CONTRACT']['REC_CONV_PTH'] = rec_conv_pth
            util.update_cm_contract_conv_data(
                db=self.mysql_db,
                target_dict=target_dict['CM_CONTRACT'],
                contract_no=json_data['CONTRACT_NO']
            )
            return target_dict
        except Exception:
            raise Exception()

    def insert_stt_result(self, target_dict):
        """
        4. Insert STT Result (MYSQL -> MSSQL)
        :param      target_dict:        Target Dictionary
        """
        self.logger.info('4. Insert STT Result (MYSQL -> MSSQL)')
        try:
            # STT 결과 조회
            results = util.select_cm_stt_rslt_detail(db=self.mysql_db, call_id=target_dict['json_data']['CALL_ID'])
            target_dict['CM_STT_RSLT_DETAIL'] = results
            bind_list = list()
            rec_id = target_dict['CM_CONTRACT']['REC_ID']
            record_file_name = target_dict['CM_CONTRACT']['REC_FILE_NM']
            for cm_stt_rslt_detail in target_dict['CM_STT_RSLT_DETAIL']:
                # 결과 정제
                spk_div_cd = 'C' if cm_stt_rslt_detail['SPEAKER_CODE'] == 'ST0001' else 'S'
                stmt_st_tm = str(timedelta(seconds=float(cm_stt_rslt_detail['START_TIME'])))
                stmt_end_tm = str(timedelta(seconds=float(cm_stt_rslt_detail['END_TIME'])))
                enc_stmt = self.cipher_object.encrypt(cm_stt_rslt_detail['SENTENCE'].encode('utf-8'))
                bind_list.append((
                    rec_id,
                    record_file_name,
                    cm_stt_rslt_detail['SENTENCE_ID'],
                    spk_div_cd,
                    stmt_st_tm,
                    stmt_end_tm,
                    enc_stmt,
                    socket.gethostname(),
                    datetime.fromtimestamp(time.time()),
                    socket.gethostname(),
                    datetime.fromtimestamp(time.time())
                ))
            self.logger.info('\t  --> Check STT results')
            del_flag = util.select_stt_results_existed(self.mssql_db, rec_id, record_file_name)
            if del_flag:
                self.logger.info('\t  --> Already existed. Delete STT results')
                util.delete_stt_results(self.mssql_db, rec_id, record_file_name)
                self.logger.info('\t  --> Done delete STT results')
            self.logger.info('\t  --> Insert STT results')
            util.insert_stt_result(self.mssql_db, bind_list)
            self.logger.info('\t  --> Done insert STT results')
        except Exception:
            raise Exception(traceback.format_exc())
        return target_dict

    def rec_conv_and_trans(self, target_dict):
        """
        5. Record Convert And Trans
        :param      target_dict:        Target Dictionary
        """
        self.logger.info("5. Record Convert And Translation")
        try:
            # 녹취파일 변환
            self.logger.info("\t1) Converting wav -> mp3")
            self.logger.info('CM_CONTRACT: {0}'.format(target_dict['CM_CONTRACT']))
            rec_path = target_dict['CM_CONTRACT']['REC_PTH']
            rec_file_nm = target_dict['CM_CONTRACT']['REC_FILE_NM']
            rec_conv_file_nm = target_dict['CM_CONTRACT']['REC_CONV_FILE_NM']
            wav_file_path = os.path.join(rec_path, rec_file_nm)
            mp3_file_path = os.path.join(rec_path, rec_conv_file_nm)
            cmd = 'ffmpeg -y -i {0} {1}'.format(wav_file_path, mp3_file_path)
            std_out, std_err = sub_process(cmd)
            # 변환된 녹취파일 이동
            conv_file_path = os.path.join(target_dict['CM_CONTRACT']['REC_CONV_PTH'], rec_conv_file_nm)
            self.logger.info("\t2) Copy mp3 file {0} -> {1}".format(mp3_file_path, conv_file_path))
            shutil.copy(mp3_file_path, conv_file_path)
            # 정보 조회
            start_time = target_dict['CALL_HISTORY']['START_TIME']
            # 백업 경로 설정
            sub_dir_name = '{0}/{1}'.format(start_time[:8], start_time[8:10])
            backup_rec_dir_path = os.path.join(self.conf.rec_bak_path, sub_dir_name)
            if not os.path.exists(backup_rec_dir_path):
                os.makedirs(backup_rec_dir_path)
            backup_rec_file_path = os.path.join(backup_rec_dir_path, rec_file_nm)
            # 녹취 파일 백업
            self.logger.info('\t3) wav file backup: {0} -> {1}'.format(wav_file_path, backup_rec_file_path))
            shutil.copy(wav_file_path, backup_rec_file_path)
            # 백업 파일 암호화
            self.logger.info('\t4) backup file encrypt: {0}'.format(backup_rec_file_path))
            self.cipher_object.encrypt_file(backup_rec_file_path)
            if os.path.exists('{0}.enc'.format(backup_rec_file_path)):
                os.remove(backup_rec_file_path)
            # mp3 파일 삭제
            self.logger.info("\t5) Remove mp3 file : {0}".format(mp3_file_path))
            os.remove(mp3_file_path)
            # 녹취업체 호출
            self.logger.info("\t6) Request to save recording information")
            start_time = target_dict['CALL_HISTORY']['START_TIME']
            end_time = target_dict['CALL_HISTORY']['END_TIME']
            file_type = 'I' if target_dict['CM_CONTRACT']['IS_INBOUND'] == 'Y' else 'O'
            json_data = target_dict['json_data']
            cust_data_class_dict = self.make_cust_data_class_dict(self.mysql_db, json_data['CAMPAIGN_ID'])
            cust_data = json.loads(target_dict['CUST_INFO']['CUST_DATA'])
            post_data = {
                'r_rec_date': start_time[:8],               # 날짜
                'r_rec_stime': start_time[8:14],                # 시작시간
                'r_rec_etime': end_time[8:14],                # 죵료시간
                'r_rec_ttime': str(int(float(target_dict['CALL_HISTORY']['DURATION']))),        # 통화시간
                'r_ext_num': target_dict['CALL_HISTORY']['SIP_USER'],  # 내선번호
                'r_call_kind': file_type,  # 콜타입
                'r_call_id': target_dict['CM_CONTRACT']['REC_ID'],  # 콜아이디
                'r_user_id': cust_data[cust_data_class_dict['상담사ID']],  # 상담사 아이디
                'r_cust_name': target_dict['CUST_INFO']['CUST_NM'],  # 고객명
                'r_cust_phone': target_dict['CUST_INFO']['CUST_TEL_NO'],     # 고객 전화번호
                'r_v_rec_fullpath': conv_file_path,
                'r_v_rec_callkey_ap': target_dict['CM_CONTRACT']['REC_ID'],   # 연동 콜키
            }
            return_value = str()
            try:
                result = requests.post(config.RecSeeConfig.host, data=post_data)
                self.logger.info('\turl: {0}'.format(config.RecSeeConfig.host))
                self.logger.info('\tdata: {0}'.format(post_data))
                self.logger.info('\tresult: {0}'.format(result.text))
                return_value = result.text
                if return_value != '1':
                    raise Exception('return value is {0}'.format(return_value))
            except Exception:
                self.logger.error(traceback.format_exc())
                self.logger.error(config.RecSeeConfig.host)
                self.logger.error(post_data)
                raise Exception(traceback.format_exc())
            if not return_value:
                raise Exception()
        except Exception:
            raise Exception(traceback.format_exc())
        return target_dict

    def enc_file(self, target_dict):
        """
        json, 녹취 파일 삭제
        :param target_dict:
        :return:
        """
        self.logger.info('6. encrypt conv file and remove json file')
        # 정보 조회
        rec_path = target_dict['CM_CONTRACT']['REC_PTH']
        rec_file_nm = target_dict['CM_CONTRACT']['REC_FILE_NM']
        rec_file_path = os.path.join(rec_path, rec_file_nm)
        # json 파일 삭제
        self.logger.info('json file remove: {0}'.format(target_dict['json_file_path']))
        os.remove(target_dict['json_file_path'])
        # 녹취 파일 삭제
        self.logger.info('wav file remove: {0}'.format(rec_file_path))
        # os.remove(rec_file_path)
        # DB Update
        util.update_cm_contract_rec_tran(
            db=self.mysql_db,
            contract_no=target_dict['json_data']['CONTRACT_NO'],
            rec_tran_yn='Y'
        )
        cust_tel_no = target_dict['CUST_INFO']['CUST_TEL_NO']
        masking_cust_tel_no = cust_tel_no.replace(cust_tel_no[-4:], '****')
        cust_nm = target_dict['CUST_INFO']['CUST_NM'].decode('utf-8')
        masking_target = cust_nm[1:-1] if cust_nm > 2 else cust_nm[1:]
        masking_cust_nm = cust_nm.replace(masking_target, '*'*len(masking_target)).encode('utf-8')
        self.logger.info('cust_tel_no masking {0} -> {1}'.format(cust_tel_no, masking_cust_tel_no))
        self.logger.info('cust_nm masking {0} -> {1}'.format(cust_nm, masking_cust_nm))
        util.update_cm_contract_for_masking(
            db=self.mysql_db,
            contract_no=target_dict['json_data']['CONTRACT_NO'],
            cust_tel_no=masking_cust_tel_no
        )
        util.update_cust_info_for_masking(
            db=self.mysql_db,
            cust_id=target_dict['json_data']['CUST_ID'],
            tel_no=masking_cust_tel_no,
            cust_nm=masking_cust_nm
        )

    def run(self):
        try:
            self.logger.info('[START] DA Postprocessing ..')
            self.set_sig_handler()
            while True:
                try:
                    self.logger.debug('-' * 100)
                    json_file_path_list = self.polling_directory()
                    for json_file_path in json_file_path_list:
                        self.logger.info('-' * 100)
                        process_step = str()
                        target_dict = {
                            'json_file_path': json_file_path
                        }
                        try:
                            process_step = '1'
                            target_dict = self.json_check(json_file_path)
                            process_step = '2'
                            target_dict = self.rec_file_check(target_dict)
                            process_step = '3'
                            target_dict = self.requests_metis(target_dict)
                            process_step = '4'
                            target_dict = self.insert_stt_result(target_dict)
                            process_step = '5'
                            target_dict = self.rec_conv_and_trans(target_dict)
                            process_step = '6'
                            self.enc_file(target_dict)
                        except Exception:
                            self.logger.error(traceback.format_exc())
                            self.error_process(process_step=process_step, target_dict=target_dict)
                except Exception:
                    self.logger.error(traceback.format_exc())
                    continue
                time.sleep(self.conf.pro_interval)
        except KeyboardInterrupt:
            self.logger.info('stopped by interrupt')
        except Exception:
            self.logger.error(traceback.format_exc())
        finally:
            if self.mssql_db:
                self.mssql_db.disconnect()
            if self.mysql_db:
                self.mysql_db.disconnect()
            self.logger.info('[E N D] DA Postprocessing stopped')
            raise Exception


#######
# def #
#######
def sub_process(cmd):
    """
    Execute subprocess
    @param      cmd:        Command
    """
    sub_pro = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    response_out, response_err = sub_pro.communicate()
    return response_out, response_err


########
# main #
########
def main():
    """
    This program that DA postprocess
    """
    da_post_daemon = DAPOSTDaemon()
    while True:
        try:
            da_post_daemon.run()
        except Exception:
            raise Exception
        finally:
            time.sleep(1)


if __name__ == '__main__':
    main()
