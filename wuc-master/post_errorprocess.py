#!/usr/bin/python
# -*- coding: utf-8 -*-

"""program"""
__author__ = "MINDsLAB"
__date__ = "creation: 2021-06-21, modification: 0000-00-00"

###########
# imports #
###########
import os
import sys
import time
import socket
import traceback
from cfg import config
from lib import logger, cipher, util
from da_postprocess import DAPOSTDaemon

###########
# options #
###########
reload(sys)
sys.setdefaultencoding("utf-8")


#########
# class #
#########
class POSTErrDaemon(DAPOSTDaemon):
    def __init__(self):
        self.conf = config.POSTErrConfig
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

    def make_job_list(self):
        result = util.select_rec_tran_n(db=self.mysql_db)
        return result

    def dec_file(self, result):
        """
        녹취 복호화 작업, 데이터 준비 작업
        :param      result:         DB Select Result
        :return:                    Target Dictionary
        """
        self.logger.info('1. decrypt wav file and wav data setting')
        # 녹취 복호화 작업
        error_dir_path = self.conf.err_tran_dir_path
        self.logger.info('\tresult: {0}'.format(result))
        start_time = result['START_TIME']
        file_name = '{0}.enc'.format(result['REC_FILE_NM'])
        wav_enc_file_path = os.path.join(error_dir_path, file_name)
        self.logger.info('\t1) decrypt wav -> {0}'.format(wav_enc_file_path))
        if not os.path.exists(wav_enc_file_path):
            self.logger.error('\t\twav file is not exists')
            raise Exception('wav file is not exists: {0}'.format(wav_enc_file_path))
        self.cipher_object.decrypt_file(wav_enc_file_path)
        # 데이터 준비 작업
        self.logger.info('\t2) wav data setting')
        target_dict = dict()
        target_dict['CM_CONTRACT'] = dict()
        target_dict['CM_CONTRACT']['REC_PTH'] = error_dir_path
        target_dict['CM_CONTRACT']['REC_FILE_NM'] = result['REC_FILE_NM']
        target_dict['CM_CONTRACT']['REC_CONV_FILE_NM'] = result['REC_CONV_FILE_NM']
        target_dict['CM_CONTRACT']['REC_CONV_PTH'] = result['REC_CONV_PTH']
        target_dict['CM_CONTRACT']['IS_INBOUND'] = result['IS_INBOUND']
        target_dict['CM_CONTRACT']['REC_ID'] = result['REC_ID']
        target_dict['CALL_HISTORY'] = dict()
        target_dict['CALL_HISTORY']['START_TIME'] = start_time
        target_dict['CALL_HISTORY']['END_TIME'] = result['END_TIME']
        target_dict['CALL_HISTORY']['DURATION'] = result['DURATION']
        target_dict['CALL_HISTORY']['SIP_USER'] = result['SIP_USER']
        target_dict['json_data'] = dict()
        target_dict['json_data']['CAMPAIGN_ID'] = result['CAMPAIGN_ID']
        target_dict['json_data']['CONTRACT_NO'] = result['CONTRACT_NO']
        target_dict['json_data']['CUST_ID'] = result['CUST_ID']
        target_dict['CUST_INFO'] = dict()
        target_dict['CUST_INFO']['CUST_DATA'] = result['CUST_DATA']
        target_dict['CUST_INFO']['CUST_NM'] = result['CUST_NM']
        target_dict['CUST_INFO']['CUST_TEL_NO'] = result['CUST_TEL_NO']
        target_dict['json_file_path'] = os.path.join(error_dir_path, result['REC_FILE_NM'].replace('.wav', '.json.enc'))
        return target_dict

    def error_process(self, process_step=str(), target_dict=dict()):
        """
        Error Process
        :param      process_step:       Process_step
        :param      target_dict:        Target Dictionary
        :return:
        """
        self.logger.error('Error Process (process step: {0})'.format(process_step))
        if process_step in ('1', '2', '3'):
            # json_file_path = target_dict['json_file_path']
            # error_dir_path = self.conf.err_tran_dir_path
            # rec_path = target_dict['CM_CONTRACT']['REC_PTH']
            # rec_file_nm = target_dict['CM_CONTRACT']['REC_FILE_NM']
            # rec_file_path = os.path.join(rec_path, rec_file_nm)
            # self.error_encrypt(json_file_path, error_dir_path)
            # self.error_encrypt(rec_file_path, error_dir_path)
            self.logger.info(target_dict)
            util.update_cm_contract_rec_tran(
                db=self.mysql_db,
                contract_no=target_dict['json_data']['CONTRACT_NO'],
                rec_tran_yn='N'
            )

    def run(self):
        try:
            self.logger.info('[START] Poset Error processing ..')
            self.set_sig_handler()
            while True:
                try:
                    self.logger.debug('-' * 100)
                    result_list = self.make_job_list()
                    for result in result_list:
                        self.logger.info('-' * 100)
                        process_step = str()
                        target_dict = {'json_data': {'CONTRACT_NO': result['CONTRACT_NO']}}
                        try:
                            process_step = '1'
                            # 녹취 복호화 작업 및 데이터 준비 작업.
                            target_dict = self.dec_file(result)
                            process_step = '2'
                            target_dict = self.rec_conv_and_trans(target_dict)
                            process_step = '3'
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
            self.logger.info('[E N D] Post Error processing stopped')
            raise Exception


#######
# def #
#######
def main():
    """
    This program that post Error process
    """
    error_post_daemon = POSTErrDaemon()
    while True:
        try:
            error_post_daemon.run()
        except Exception:
            raise Exception
        finally:
            time.sleep(1)


########
# main #
########
if __name__ == '__main__':
    main()