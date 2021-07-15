#!/usr/bin/python
# -*- coding:utf-8 -*-

"""program"""
__author__ = "MINDsLAB"
__date__ = "creation: 2021-06-16, modification: 0000-00-00"

###########
# imports #
###########
import os
import sys
import time
import shutil
import traceback
from datetime import datetime
from cfg import config
from lib import logger

###########
# options #
###########
reload(sys)
sys.setdefaultencoding("utf-8")


#######
# def #
#######
def del_garbage(log, delete_file_path):
    """
    Delete directory or file
    :param      log:                    Logger
    :param      delete_file_path:       Input Path
    """
    if os.path.exists(delete_file_path):
        try:
            log.info('delete {0}'.format(delete_file_path))
            if os.path.isfile(delete_file_path):
                os.remove(delete_file_path)
            if os.path.isdir(delete_file_path):
                shutil.rmtree(delete_file_path)
        except Exception:
            exc_info = traceback.format_exc()
            log.error("Can't delete {0}".format(delete_file_path))
            log.error(exc_info)


def delete_file(log, ts, target_info_dict):
    """
    Delete file
    :param      log:                    Logger
    :param      ts:                     System time
    :param      target_info_dict:       Target information dictionary
    """
    # Delete record file
    target_dir_path = target_info_dict.get('dir_path')
    if target_dir_path[-1] == '/':
        target_dir_path = target_dir_path[:-1]
    mtn_period = int(target_info_dict.get('mtn_period'))
    w_ob = os.walk(target_dir_path)
    for dir_path, sub_dirs, files in w_ob:
        if len(files) == 0 and len(sub_dirs) == 0:
            if dir_path:
                del_garbage(log, dir_path)
        for file_path in files:
            target_path = os.path.join(dir_path, file_path)
            period = (datetime.now() - datetime.fromtimestamp(os.path.getctime(target_path))).days
            log.info('period: {0}, 조건: {1}'.format(period, period >= mtn_period))
            if period >= mtn_period:
                if target_path:
                    del_garbage(log, target_path)


def elapsed_time(start_time):
    """
    elapsed time
    :param      start_time:         date object
    :return:                        Required time (type: datetime)
    """
    end_time = datetime.fromtimestamp(time.time())
    required_time = end_time - start_time
    return required_time


def processing(conf, target_dir_list):
    """
    processing
    :param      conf:                   Config
    :param      target_dir_list:        Target directory list
    """
    ts = time.time()
    st = datetime.fromtimestamp(ts)
    # Add logging
    log = logger.get_timed_rotating_logger(
        logger_name=conf.logger_name,
        log_dir_path=conf.log_dir_path,
        log_file_name=conf.log_file_name,
        backup_count=conf.backup_count,
        log_level=conf.log_level
    )
    log.info("-" * 100)
    log.info("Start delete log and output file")
    try:
        for target_info_dict in target_dir_list:
            log.info("Directory path: {0}, Maintenance period: {1}".format(
                target_info_dict['dir_path'], target_info_dict['mtn_period']))
            # Delete file
            try:
                delete_file(log, ts, target_info_dict)
            except Exception:
                exc_info = traceback.format_exc()
                log.error(exc_info)
                continue
    except Exception:
        exc_info = traceback.format_exc()
        log.error(exc_info)
    finally:
        log.info("END.. Start time = {0}, The time required = {1}".format(st, elapsed_time(st)))
        for handler in log.handlers:
            handler.close()
            log.removeHandler(handler)


########
# main #
########
def main():
    """
    This is a program that delete log and output file
    """
    try:
        conf = config.DELConfig
        target_dir_list = conf.target_directory_list
        processing(conf, target_dir_list)
    except Exception:
        exc_info = traceback.format_exc()
        print(exc_info)
        sys.exit(1)


if __name__ == '__main__':
    main()
