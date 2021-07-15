#!/usr/bin/python
# -*- coding: utf-8 -*-

"""program"""
__author__ = "MINDsLAB"
__date__ = "creation: 2021-06-16, modification: 0000-00-00"

###########
# imports #
###########
import time
import signal
import argparse
import subprocess

#############
# constants #
#############
ONE_DAY_IN_SECONDS = 60 * 60 * 24


#########
# class #
#########
class GracefullKiller:
    kill_now = False

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        self.kill_now = True


#######
# def #
#######
def sub_process(cmd):
    """
    Execute subprocess
    :param      cmd:        Command
    """
    sub_pro = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    response_out, response_err = sub_pro.communicate()
    if len(response_out) > 0:
        print(response_out)
    if len(response_err) > 0:
        print(response_err)


########
# main #
########
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', action='store', dest='docker_name', default=False, type=str, help='docker name')
    parser.add_argument('-c', action='store', dest='config_path', default=False, type=str, help='server.cfg path')
    parser.add_argument('-p', action='store', dest='port', default=False, type=str, help='Port')
    arguments = parser.parse_args()
    killer = GracefullKiller()
    start_cmd = 'docker exec -i {0} /root/wav2letter/build/Server --flagsfile {1} --port {2}'.format(
        arguments.docker_name, arguments.config_path, arguments.port)
    sub_process(start_cmd)
    while not killer.kill_now:
        time.sleep(ONE_DAY_IN_SECONDS)
    stop_cmd = 'docker exec -i {0} pkill -9 -ef Server'.format(arguments.docker_name)
    print(stop_cmd)
    sub_process(stop_cmd)
    print('complete')
