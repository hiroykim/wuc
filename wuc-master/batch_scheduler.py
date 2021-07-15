#!/usr/bin/python
# -*- coding:utf-8 -*-

"""program"""
__author__ = "MINDsLAB"
__date__ = "creation: 2021-06-16, modification: 0000-00-00"

###########
# imports #
###########
import sys
import time
import traceback
import subprocess
from apscheduler.schedulers.background import BackgroundScheduler
from cfg import config
from lib import logger

###########
# options #
###########
reload(sys)
sys.setdefaultencoding("utf-8")


#########
# class #
#########
class Scheduler(object):
    def __init__(self):
        self.conf = config.BatchConfig
        self.logger = logger.get_timed_rotating_logger(
            logger_name=self.conf.logger_name,
            log_dir_path=self.conf.log_dir_path,
            log_file_name=self.conf.log_file_name,
            backup_count=self.conf.backup_count,
            log_level=self.conf.log_level
        )
        self.sched = BackgroundScheduler()
        self.sched.start()
        self.job_id = str()

    def sub_process(self, cmd):
        """
        Execute subprocess
        :param      cmd:        Command
        """
        self.logger.info("Command -> {0}".format(cmd))
        sub_pro = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # subprocess 가 끝날때까지 대기
        response_out, response_err = sub_pro.communicate()
        if len(response_out) > 0:
            self.logger.debug(response_out)
        if len(response_err) > 0:
            self.logger.debug(response_err)
        return response_out

    def scheduler(self, job_id, target):
        if type(target) is str:
            target_list = target.split(' ')
            self.logger.info("Scheduler Start : ({0}) {1}".format(' '.join(target_list[:5]), ' '.join(target_list[5:])))
            bind_dict = {
                'second': 0,
                'minute': target_list[0],
                'hour': target_list[1],
                'day': target_list[2],
                'month': target_list[3],
                'day_of_week': target_list[4],
                'command': ' '.join(target_list[5:])
            }
        else:
            bind_dict = dict(target)
        try:
            self.sched.add_job(
                self.sub_process,
                'cron',
                second=bind_dict['second'],
                minute=bind_dict['minute'],
                hour=bind_dict['hour'],
                day=bind_dict['day'],
                month=bind_dict['month'],
                day_of_week=bind_dict['day_of_week'],
                id=job_id,
                args=(bind_dict['command'],)
            )
        except Exception:
            self.logger.error('Scheduler Start Failed: {0}'.format(target))
            self.logger.error(traceback.format_exc())


########
# main #
########
def main():
    """
    This is a program that Batch Scheduler
    """
    try:
        scheduler = Scheduler()
        idx = 0
        for target in scheduler.conf.target:
            scheduler.scheduler(str(idx), target)
            idx += 1
        scheduler.logger.info('Start main process...')
        while True:
            time.sleep(0.1)
    except Exception:
        print(traceback.format_exc())


if __name__ == '__main__':
    main()
