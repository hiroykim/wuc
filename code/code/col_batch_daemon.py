#!/usr/bin/python
# -*- coding: utf-8 -*-

"""program"""
__author__ = "MINDsLAB"
__date__ = "creation: 2021-06-02, modification: 0000-00-00"

###########
# imports #
###########
import os
import sys
import time
import json
import shutil
import signal
import socket
import requests
import traceback
import collections
from cfg import config
from lib import logger, db_connection, filelock, util
from datetime import datetime, date

###########
# options #
###########
reload(sys)
sys.setdefaultencoding("utf-8")


#########
# class #
#########
class CollectorBatchDaemon(object):
    def __init__(self, log):
        self.conf = config.CollectorBatchConfig
        self.logger = log
        self.mysql_db = self.connect_db('MYSQL', config.MYConfig)
        self.line_cnt = int()
        self.error_cnt = int()
        self.upload_cnt = int()

    def connect_db(self, db_type, db_conf):
        db = str()
        flag = True
        while flag:
            try:
                self.logger.info('Try connecting to {0} DB ...'.format(db_type))
                if db_type.upper() == 'MYSQL':
                    db = db_connection.MYSQL(db_conf)
                    flag = False
                else:
                    raise Exception('Not supported db ..(MYSQL)')
                self.logger.info('Success connect to {0} DB'.format(db_type))
            except Exception:
                err_str = traceback.format_exc()
                self.logger.error(err_str)
                time.sleep(60)
        return db

    def signal_handler(self, sig, frame):
        if frame:
            pass
        if sig == signal.SIGHUP:
            return
        if sig == signal.SIGTERM or sig == signal.SIGINT:
            if self.mysql_db:
                self.mysql_db.conn.commit()
            self.logger.info('stopped by interrupt')
            sys.exit(0)

    def set_sig_handler(self):
        signal.signal(signal.SIGTSTP, signal.SIG_IGN)
        signal.signal(signal.SIGTTOU, signal.SIG_IGN)
        signal.signal(signal.SIGTTIN, signal.SIG_IGN)
        signal.signal(signal.SIGHUP, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def make_file_list(self):
        """
        Make sorted batch file list
        :return:        Sorted batch file list
        """
        self.logger.debug("Make batch file list")
        target_dir_path = config.CollectorBatchConfig.batch_file_dir_path
        self.logger.debug("Batch file directory list = {0}".format(target_dir_path))
        if not os.path.exists(target_dir_path):
            self.logger.error("Batch file directory is not exist. -> {0}".format(target_dir_path))
            return list()
        # ?????? ?????? ????????? ??????
        file_list = list()
        for dir_path, sub_dirs, files in os.walk(target_dir_path):
            for file_name in files:
                if file_name.endswith(config.CollectorBatchConfig.batch_file_ext):
                    file_path = os.path.join(dir_path, file_name)
                    # ?????? ????????? ????????? ????????? ????????? ?????? ?????? ??? ??????
                    while True:
                        file_size = os.path.getsize(file_path)
                        time.sleep(1)
                        if file_size == os.path.getsize(file_path):
                            file_list.append(file_path)
                            break
        # ?????? ?????? ?????? ?????? ?????? ?????? ??????
        self.logger.debug("Batch file list, sorted by last modified time.")
        sorted_file_list = sorted(file_list, key=os.path.getmtime, reverse=False)
        return sorted_file_list

    def error_process(self, file_path):
        """
        Error file process
        :param      file_path:      Batch File Path
        """
        self.error_cnt += 1
        try:
            self.logger.error("Error process. [Batch File = {0}]".format(file_path))
            # Error file ??????
            file_name = os.path.basename(file_path)
            backup_file_path = os.path.join(config.CollectorBatchConfig.error_dir_path, file_name)
            if not os.path.exists(config.CollectorBatchConfig.error_dir_path):
                os.makedirs(config.CollectorBatchConfig.error_dir_path)
            if os.path.exists(file_path):
                if os.path.exists(backup_file_path):
                    os.remove(backup_file_path)
                shutil.copy(file_path, backup_file_path)
                self.logger.error("\tComplete Copy Error file -> {0}".format(backup_file_path))
            else:
                self.logger.error("\tFile is not exists")
        except Exception:
            exc_info = traceback.format_exc()
            self.logger.critical("Critical error {0}".format(exc_info))

    def check_raw_data(self, sorted_batch_list):
        """
        Check data
        :param      sorted_batch_list:      batch file list
        :return:                            Checked batch data
        """
        self.logger.debug("-" * 100)
        self.logger.debug("Check raw data (Batch)")
        batch_data_dict = collections.OrderedDict()
        # TODO Input??????????????? ????????? Dictionary ??????
        for file_path in sorted_batch_list:
            file_name_ext = os.path.basename(file_path)
            line_count = 0
            try:
                self.logger.info("Open batch file.[{0}]".format(file_path))
                file_name = os.path.splitext(file_name_ext)[0]
                ob_call_dtm = file_name.split('_')[1]
                start_dtm = '{0}-{1}-{2}'.format(ob_call_dtm[:4], ob_call_dtm[4:6], ob_call_dtm[6:8])
                dispatch_time = '{0}:{1}:00'.format(ob_call_dtm[8:10], ob_call_dtm[10:12])
                file_lines = open(file_path)
                for line in file_lines:
                    try:
                        line_count += 1
                        line_list = line.split('\t')
                        key = '{0}!@#${1}'.format(file_path, line_count)
                        batch_data_dict[key] = {
                            '?????????ID': self.conf.campaign_id,                 # ????????? ID
                            '????????????ID': line_list[0].strip(),                 # ???????????? ID
                            '???????????????': '9{0}'.format(line_list[1].strip()),   # ???????????????
                            '?????????': line_list[2].strip(),                    # ?????????
                            '??????????????????': line_list[3].strip(),                 # ??????????????????
                            '????????????': line_list[4].strip(),                   # ????????????
                            '????????????': line_list[5].strip(),                   # ????????????
                            '?????????ID': line_list[6].strip(),                  # ?????????ID (???????????????)
                            '????????????': start_dtm,                              # ????????????
                            '????????????': start_dtm,                              # ????????????
                            '????????????': dispatch_time,                          # ????????????
                            '????????????': 0,                                      # ????????????
                            '????????????': '',                                     # ????????????
                            '????????????_?????????': file_name                           # ????????????_?????????
                        }
                    except Exception:
                        exc_info = traceback.format_exc()
                        self.logger.error(exc_info)
                        self.error_process(file_path)
            except Exception:
                exc_info = traceback.format_exc()
                self.logger.error(exc_info)
                self.error_process(file_path)
            finally:
                self.line_cnt += line_count
                backup_file_path = os.path.join(config.CollectorBatchConfig.backup_dir_path, file_name_ext)
                if not os.path.exists(config.CollectorBatchConfig.backup_dir_path):
                    os.makedirs(config.CollectorBatchConfig.backup_dir_path)
                self.logger.info('Target file Backup ({0}->{1})'.format(file_path, backup_file_path))
                shutil.copy(file_path, backup_file_path)
        return batch_data_dict

    def upload_data_to_db(self, checked_file_data_dict):
        """
        Upload data to database
        :param      checked_file_data_dict:         Checked file data dictionary
        """
        self.logger.debug("batch file data upload to DB")
        file_name_dict = dict()
        for key, file_data in checked_file_data_dict.items():
            file_path, line_number = key.split('!@#$')
            try:
                self.logger.debug("Target batch file = {0}, line_number = {1}".format(file_path, line_number))
                # cust_data ??????
                cust_data_class_dict = make_cust_data_class_dict(self.mysql_db, file_data['?????????ID'])
                cust_data = {
                    cust_data_class_dict['??????????????????']: file_data['??????????????????'],
                    cust_data_class_dict['????????????']: file_data['????????????'],
                    cust_data_class_dict['????????????ID']: file_data['????????????ID'],
                    cust_data_class_dict['????????????']: file_data['????????????'],
                    cust_data_class_dict['?????????ID']: file_data['?????????ID'],
                    cust_data_class_dict['????????????']: file_data['????????????'],
                    cust_data_class_dict['????????????']: file_data['????????????'],
                    cust_data_class_dict['????????????_?????????']: file_data['????????????_?????????'],
                }
                data_check_flag = True
                for key, cust_data_class_id in cust_data_class_dict.items():
                    if not key in file_data:
                        data_check_flag = False
                if not data_check_flag:
                    self.logger.error('file_data is wrong..')
                    self.logger.error('file_data: {0}'.format(file_data))
                    self.logger.error('cust_data_class_dict: {0}'.format(cust_data))
                # ???????????? INSERT
                util.insert_cust_info(
                    db=self.mysql_db,
                    campaign_id=file_data['?????????ID'],
                    cust_nm=file_data['?????????'],
                    cust_tel_no=file_data['???????????????'],
                    cust_data=json.dumps(cust_data),
                    target_yn=None,
                    blacklist_yn=None,
                    correct_yn=None
                )
                # ??? ?????? INSERT
                cust_id = util.select_cust_id(
                    db=self.mysql_db
                )
                if not cust_id:
                    self.logger.error('max cust_id is not exist -> {0}'.format(file_data))
                    continue
                util.insert_cm_contract(
                    db=self.mysql_db,
                    campaign_id=file_data['?????????ID'],
                    cust_id=cust_id,
                    tel_no=file_data['???????????????'],
                    cust_op_id=None,
                    prod_id=None,
                    call_try_count='0',
                    last_call_id=None,
                    is_inbound='N',
                    task_seq=None,
                    use_yn='y'
                )
                # ??? ?????? ?????? INSERT
                start_dtm = file_data['????????????']
                week_day = date(int(start_dtm[:4]), int(start_dtm[5:7]), int(start_dtm[8:10])).isoweekday()
                week_day += 1
                if week_day == 8:
                    week_day = 1
                cd_name = '{0}_{1}_{2}'.format(start_dtm, file_data['????????????'], file_data['????????????ID'])
                util.insert_auto_call_condition(
                    db=self.mysql_db,
                    start_dtm=start_dtm,
                    end_dtm=file_data['????????????'],
                    dispatch_time=file_data['????????????'],
                    ob_call_status=None,
                    call_try_count=None,
                    creator='col_batch_daemon',
                    campaign_id=file_data['?????????ID'],
                    progress_status=None,
                    active_status='1',
                    use_yn='Y',
                    week_day=week_day,
                    cd_desc=cd_name,
                    cd_name=cd_name
                )
                # ??? ?????? ?????? Custom INSERT
                auto_call_condition_id = util.select_auto_call_condition_id(
                    db=self.mysql_db
                )
                if not auto_call_condition_id:
                    self.logger.error('max auto_call_condition_id is not exist -> {0}'.format(file_data))
                    continue
                for key, cust_data_class_id in cust_data_class_dict.items():
                    util.insert_auto_call_condition_custom(
                        db=self.mysql_db,
                        cust_data_class_id=cust_data_class_id,
                        auto_data_condition_id=auto_call_condition_id,
                        data_value=file_data[key],
                        use_yn='Y'
                    )
                # ?????? ?????? ?????? ???????????? ??????.
                file_name = os.path.basename(file_path)
                if file_name not in file_name_dict:
                    file_name_dict[file_name] = True
                    backup_file_path = os.path.join(config.CollectorBatchConfig.backup_dir_path, file_name)
                    self.logger.debug('Target file Backup ({0}->{1})'.format(file_path, backup_file_path))
                    shutil.copy(file_path, backup_file_path)
                self.upload_cnt += 1
            except Exception:
                exc_info = traceback.format_exc()
                self.logger.error(exc_info)
                self.logger.error('Error -> Key: {0}, file_data: {1}'.format(key, file_data))
                self.mysql_db.conn.rollback()
                self.error_process(file_path)
                continue

    @staticmethod
    def elapsed_time(sdate):
        """
        elapsed time
        :param      sdate:      date object
        :return:                Required time(type : datetime)
        """
        end_time = datetime.now()
        if not sdate or len(sdate) < 14:
            return 0, 0, 0, 0
        start_time = datetime(int(sdate[:4]), int(sdate[4:6]), int(sdate[6:8]), int(sdate[8:10]), int(sdate[10:12]),
                              int(sdate[12:14]))
        required_time = end_time - start_time
        return required_time

    def delete_file(self, batch_list):
        """
        Delete file
        :param      batch_list:         Batch file path list
        """
        self.logger.info('batch file delete')
        for file_path in batch_list:
            self.logger.info('\tfile delete -> {0}'.format(file_path))
            os.remove(file_path)

    def run(self):
        try:
            self.logger.info('[START] Collector Batch file daemon process started')
            self.set_sig_handler()
            while True:
                dt = datetime.fromtimestamp(time.time()).strftime('%Y%m%d%H%M%S')
                # Make batch file list
                sorted_batch_list = self.make_file_list()
                if len(sorted_batch_list) > 0:
                    # file data check
                    checked_file_data_dict = self.check_raw_data(sorted_batch_list)
                    # Upload batch data to db
                    self.upload_data_to_db(checked_file_data_dict)
                    self.delete_file(sorted_batch_list)
                    self.logger.info("Total batch target count = {0}, line_count = {1}, upload_count = {2}, "
                                     "error_count = {3}, The time required = {4}".format(
                        len(sorted_batch_list), self.line_cnt, self.upload_cnt, self.error_cnt, self.elapsed_time(dt)))
                    self.line_cnt = int()
                    self.upload_cnt = int()
                    self.error_cnt = int()
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info('stopped by interrupt')
        except Exception:
            self.logger.error(traceback.format_exc())
        finally:
            if self.mysql_db:
                self.mysql_db.disconnect()
            self.logger.info('[E N D] Collector Batch daemon process stopped')


#######
# def #
#######
def make_cust_data_class_dict(mysql_db, campaign_id):
    cust_data_class_list = util.select_cust_data_class(mysql_db, campaign_id)
    cust_data_class_dict = dict()
    for cust_data_class in cust_data_class_list:
        cust_data_class_dict[cust_data_class['COLUMN_KOR'].encode('utf-8')] = str(cust_data_class['CUST_DATA_CLASS_ID'])
    return cust_data_class_dict


########
# main #
########
def main():
    """
    This is a program that Collector Batch Daemon process
    """
    # Set logger
    conf = config.CollectorBatchConfig
    log = logger.get_timed_rotating_logger(
        logger_name=conf.logger_name,
        log_dir_path=conf.log_dir_path,
        log_file_name=conf.log_file_name,
        backup_count=conf.backup_count,
        log_level=conf.log_level
    )
    col_batch_daemon = CollectorBatchDaemon(log)
    while True:
        try:
            with filelock.FileLock(conf.lock_file_path):
                col_batch_daemon.run()
        except Exception as e:
            if 'Timeout occured' in e.message:
                # lock file ?????? read
                fd = os.open('{0}.lock'.format(conf.lock_file_path), os.O_RDWR)
                fdo = os.fdopen(fd, "rb")
                lock_process = fdo.readlines()[0].strip()
                # ?????? ?????? ????????? ?????? ??????
                current_idx = -1
                for svr in conf.svr_list:
                    if svr['proc_svr'] == socket.gethostname():
                        current_idx = conf.svr_list.index(svr)
                if current_idx == -1:
                    error_message = "This Server is not exist in svr_list config"
                    print(error_message)
                    log.error(error_message)
                    raise Exception(error_message)
                # ?????? ??????????????? ??? ????????? ?????? ?????? ??????
                if lock_process == socket.gethostname():
                    check_target_server = conf.svr_list[current_idx]
                    host = 'http://{0}:8787/check_pro'.format(check_target_server['host'])
                    payload = {'pro_name': os.path.basename(os.path.splitext(__file__)[0])}
                    result = requests.post(host, data=payload)
                    pro_cnt = json.loads(result.text)
                    if int(pro_cnt) == 1:
                        os.remove('{0}.lock'.format(conf.lock_file_path))
                        log.info("remove {0}".format(lock_process))
                # ?????? ??????
                while True:
                    # ?????? ??????
                    check_target_server = conf.svr_list[current_idx - 1]
                    host = 'http://{0}:8787/check_pro'.format(check_target_server['host'])
                    payload = {'pro_name': os.path.basename(os.path.splitext(__file__)[0])}
                    process_status = False
                    try:
                        result = requests.post(host, data=payload)
                        pro_cnt = json.loads(result.text)
                        if pro_cnt > 0:
                            process_status = True
                    except Exception:
                        log.error(traceback.format_exc())
                        process_status = False
                    # ?????? ???????????? ??????
                    if process_status:
                        break
                    # ?????????, ???????????? ????????? ?????? ????????? ??????
                    if lock_process == check_target_server['proc_svr']:
                        os.remove('{0}.lock'.format(conf.lock_file_path))
                        log.info("remove {0}".format(lock_process))
                        break
                    # ?????????, ?????? ?????? ?????? ??????
                    current_idx -= 1
                    if current_idx == -1:
                        current_idx = len(conf.svr_list) - 1
                log.info("Blocking .. {0}".format(lock_process))
            else:
                raise Exception(traceback.format_exc())
        finally:
            time.sleep(1)


if __name__ == '__main__':
    main()
