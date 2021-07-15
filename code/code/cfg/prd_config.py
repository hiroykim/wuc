#!/usr/bin/python
# -*- coding: utf-8 -*-


class CollectorBatchConfig(object):
    logger_name = 'COL_BATCH_DAEMON'
    log_dir_path = '/logs/maum/collector'
    log_file_name = 'collector_batch_daemon.log'
    backup_count = 30
    log_level = 'info'
    lock_file_path = '/appl/maum/cfg/.col_batch'
    batch_file_dir_path = '/ondemandfile/tm/ai/'
    batch_file_ext = '.dat'
    backup_dir_path = '/DATA/output/batch_file_backup'
    error_dir_path = '/DATA/output/batch_file_error'
    svr_list = [
        {'host': '10.20.20.65', 'proc_svr': 'ntmwuc1p', 'pro_max_limit': 15},
    ]
    campaign_id = '1'


class MYConfig(object):
    host = '10.20.20.65'
    host_list = ['10.20.20.65', ]
    user = 'minds'
    pd = '/appl/maum/cfg/.mystt'     # Mindslab!1
    ps_path = '/appl/maum/cfg/.meritz'
    port = 3306
    charset = 'utf8'
    database = 'fast_aicc'
    connect_timeout = 5
    reconnect_interval = 1


class DaConfig(object):
    logger_name = 'Meritz_DA'
    log_dir_path = '/logs/maum/DA'
    log_level = 'debug'
    task_seq_dict = {
        '일정예약성공종결': 'S001',
        '본인부정종결': 'S002',
        '타인종결': 'S003',
        '부재종결': 'S004',
        '정보안내종결': 'S005',
        '회피종결': 'S006',
        '반문종결': 'S007',
        '거절종결': 'S008',
        'DNC종결': 'S009',
        '담당자응대종결': 'S010',
        '무응답종결': 'S011',
        '문자종결': 'S012',
        '운전종결': 'S013',
        '최대반복초과종결': 'S014',
        '기타종결': 'S015'
    }
    success_cd_dict = {
        '01': ('성공', ['S001', 'S002', 'S012']),
        '02': ('실패',
               ['S002', 'S003', 'S004', 'S005', 'S006', 'S007', 'S008', 'S009', 'S010', 'S011', 'S013', 'S014', 'S015'])
    }
    json_dir_path = '/DATA/output/record'


class DELConfig(object):
    target_directory_list = [
        {
            'dir_path': '/logs/maum/DA',
            'mtn_period': 365
        },
        {
            'dir_path': '/DATA/output/batch_file_backup',
            'mtn_period': 30
        },
        {
            'dir_path': '/DATA/output/batch_file_error',
            'mtn_period': 365
        },
        {
            'dir_path': '/DATA/output/record_backup',
            'mtn_period': 1
        },
        {
            'dir_path': '/DATA/output/err_trans',
            'mtn_period': 365
        },
        {
            'dir_path': '/DATA/output/err_record',
            'mtn_period': 365
        },
        {
            'dir_path': '/DATA/output/record',
            'mtn_period': 14
        }
    ]
    logger_name = 'DELETE'
    log_dir_path = '/logs/maum/delete'
    log_file_name = 'delete_file.log'
    backup_count = 30
    log_level = 'debug'


class BatchConfig(object):
    logger_name = 'BatchScheduler'
    log_dir_path = '/logs/maum/batch'
    log_file_name = 'batch_scheduler.log'
    backup_count = 30
    log_level = 'info'
    target = [
        # '* * * * * echo test',
        # {
        #     'seconds': '*/5',       # (int|str) - seconds (0-59)
        #     'minute': '*',          # (int|str) - minute (0-59)
        #     'hour': '*',            # (int|str) - hour (0-23)
        #     'day': '*',             # (int|str) - day of the (1-31)
        #     'month': '*',           # (int|str) - month (1-12)
        #     'day_of_week': '*',     # (int|str) - number or name of weekday (0-6 or mon,tue,wed,thu,fri,sat,sun)
        #     'command': ''           # (str) - command
        # },
        '0 1 * * * python /appl/maum/delete_file.py'
    ]


class MSConfig(object):
    host = '10.20.40.73'
    host_list = ['10.20.40.73']
    user = 'stauser'
    pd = '/appl/maum/cfg/.stt'
    ps_path = '/appl/maum/cfg/.meritz'
    port = 1433
    charset = 'utf8'
    database = 'DBSTTS'
    login_timeout = 5
    reconnect_interval = 20


class DAPOSTConfig(object):
    logger_name = 'DAPOST'
    log_dir_path = '/logs/maum/da_post'
    log_file_name = 'da_postprocess.log'
    backup_count = 8
    log_level = 'info'
    pro_interval = 3
    polling_dir_path = '/DATA/output/record'
    err_json_dir_path = '/DATA/output/err_record/err_json'
    err_metis_dir_path = '/DATA/output/err_record/err_metis'
    rec_conv_path = '/MD_RecAct/REC/RecSee_Data/A011'
    err_tran_dir_path = '/DATA/output/err_trans'
    rec_bak_path = '/DATA/output/record_backup'


class AESConfig(object):
    pd = '/appl/maum/cfg/.aes'
    ps_path = '/appl/maum/cfg/.meritz'


class MetisConfig(object):
    host = "http://ntm.meritzfire.com/tm.fw.onweb/registAiTcRsl.do"


class RecSeeConfig(object):
    host = "http://cirec.meritzfire.com:28884/"


class POSTErrConfig(object):
    logger_name = 'POSTERR'
    log_dir_path = '/logs/maum/post_err'
    log_file_name = 'post_errprcoess.log'
    backup_count = 30
    log_level = 'info'
    err_tran_dir_path = '/DATA/output/err_trans'
    rec_bak_path = '/DATA/output/record_backup'
    pro_interval = 3600


class METISReqConfig(object):
    logger_name = 'METISREQ'
    log_dir_path = '/logs/maum/metis_req'
    log_file_name = 'metis_req_process.log'
    backup_count = 30
    log_level = 'info'
    pro_interval = 1
    select_interval = -10
