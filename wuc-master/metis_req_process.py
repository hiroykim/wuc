#!/usr/bin/python
# -*- coding: utf-8 -*-

"""program"""
__author__ = "MINDsLAB"
__date__ = "creation: 2021-07-06, modification: 0000-00-00"

###########
# imports #
###########
import os
import sys
import json
import time
import requests
import traceback
from cfg import config
from lib import logger, util
from da_postprocess import DAPOSTDaemon

###########
# options #
###########
reload(sys)
sys.setdefaultencoding("utf-8")


#########
# class #
#########
class METISReqDaemon(DAPOSTDaemon):
    def __init__(self):
        self.conf = config.METISReqConfig
        self.logger = logger.get_timed_rotating_logger(
            logger_name=self.conf.logger_name,
            log_dir_path=self.conf.log_dir_path,
            log_file_name=self.conf.log_file_name,
            backup_count=self.conf.backup_count,
            log_level=self.conf.log_level
        )
        self.mysql_db = self.connect_db('MYSQL', config.MYConfig)
        self.mssql_db = False

    def make_job_list(self):
        result = util.select_dial_result_detail_null(db=self.mysql_db, interval=self.conf.select_interval)
        return result

    def data_setting(self, result):
        """
        데이터 준비 작업, DB UPDATE
        :param      result:         DB Select Result
        :return:                    Target Dictionary
        """
        self.logger.info('1. data setting and db update')
        # 데이터 업데이트 대상
        success_cd = '02'
        success_nm = '실패'
        task_seq = 'F001'
        task_seq_nm = ''
        dial_result_detail = result['DIAL_RESULT']
        if dial_result_detail == '480':
            dial_result_detail = '600'
        cust_react = ''
        call_try_count = 1
        rec_file_name = ''
        rec_path = ''
        # 데이터 준비 작업
        self.logger.info('\t1) data setting')
        target_dict = dict()
        target_dict['json_data'] = dict()
        target_dict['json_data']['CUST_ID'] = result['CUST_ID']
        target_dict['json_data']['CALL_ID'] = result['CALL_ID']
        target_dict['json_data']['CAMPAIGN_ID'] = result['CAMPAIGN_ID']
        target_dict['json_data']['CONTRACT_NO'] = result['CONTRACT_NO']
        target_dict['CALL_HISTORY'] = dict()
        target_dict['CALL_HISTORY']['START_TIME'] = result['START_TIME']
        target_dict['CALL_HISTORY']['DIAL_RESULT_DETAIL'] = dial_result_detail
        target_dict['CALL_HISTORY']['DURATION'] = result['DURATION']
        target_dict['CM_CONTRACT'] = dict()
        target_dict['CM_CONTRACT']['SUCCESS_CD'] = success_cd
        target_dict['CM_CONTRACT']['TASK_SEQ'] = task_seq
        target_dict['CM_CONTRACT']['CUST_REACT'] = cust_react
        # DB 업데이트
        # CM_CONTRACT UPDATE
        util.update_cm_contract(
            db=self.mysql_db,
            contract_no=result['CONTRACT_NO'],
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
            db=self.mysql_db,
            call_id=result['CALL_ID'],
            dial_result_detail=dial_result_detail
        )
        return target_dict

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
            start_time = target_dict['CALL_HISTORY']['START_TIME']
            post_data = {
                'cnsCusId': cust_data[cust_data_class_dict['상담고객ID']],  # 상담고객ID
                'aiSnroRslCd': target_dict['CM_CONTRACT']['SUCCESS_CD'],    # AI시나리오결과코드
                'aiSnroRslDtl': target_dict['CM_CONTRACT']['TASK_SEQ'],     # AI시나리오결과상세
                'aiTcRslCd': target_dict['CALL_HISTORY']['DIAL_RESULT_DETAIL'],        # AI통화결과코드
                'cusRact': target_dict['CM_CONTRACT']['CUST_REACT'],          # 고객반응
                'tcHr': str(int(float(target_dict['CALL_HISTORY']['DURATION']))),             # 통화시간 (초단위)
                'tcStTm': start_time,           # 통화시작시간 (YYYYMMDDHH24MISS)
                'tcEdTm': target_dict['CALL_HISTORY']['END_TIME'],                  # 통화종료시간 (YYYYMMDDHH24MISS)
                'fileNm': str(),           # 녹취파일명
            }
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
            return target_dict
        except Exception:
            raise Exception()

    def run(self):
        try:
            self.logger.info('[START] METIS Request processing for null DIAL_RESULT_DETAIL')
            self.set_sig_handler()
            while True:
                try:
                    self.logger.debug('-' * 100)
                    result_list = self.make_job_list()
                    for result in result_list:
                        self.logger.info('-' * 100)
                        try:
                            # 데이터 정리 및 DB UPDATE
                            target_dict = self.data_setting(result)
                            # METIS Requests
                            self.requests_metis(target_dict)
                        except Exception:
                            self.logger.error(traceback.format_exc())
                            time.sleep(10)
                except Exception:
                    self.logger.error(traceback.format_exc())
                    continue
                time.sleep(self.conf.pro_interval)
        except KeyboardInterrupt:
            self.logger.info('stopped by interrupt')


#######
# def #
#######

########
# main #
########
def main():
    """
    This program that METIS Requests process for NULL DIAL_RESULT_DETAIL
    """
    metis_req_daemon = METISReqDaemon()
    while True:
        try:
            metis_req_daemon.run()
        except Exception:
            raise Exception
        finally:
            time.sleep(1)


if __name__ == '__main__':
    main()
