#!/usr/bin/python
# -*- coding: utf-8 -*-

"""program"""
__author__ = "MINDsLAB"
__date__ = "creation: 2020-09-09, modification: 2020-09-09"

###########
# imports #
###########
import sys
import socket
import subprocess
from flask import Flask, request
from flask_cors import CORS
from flask_restful import Api, reqparse, Resource

###########
# options #
###########
reload(sys)
sys.setdefaultencoding("utf-8")


#########
# class #
#########
class CheckProAPI(Resource):
    def __init__(self):
        self.pro_name = request.form.get('pro_name')

    def post(self):
        return check_process(self.pro_name)


class CheckSupervisorAPI(Resource):
    @staticmethod
    def post():
        return check_supervisor()


#######
# def #
#######
def check_process(pro_name):
    """
    Extract number or process running
    :param         pro_name:         Process name
    :return:                         Number of process running
    """
    pro_list = subprocess.check_output(['ps', 'uaxw']).splitlines()
    pro_cnt = len([pro for pro in pro_list if pro_name in pro])
    return pro_cnt


def check_supervisor():
    """
    Check Supervisor status
    :return:         Supervisor status
    """
    sub_pro = subprocess.Popen('svctl status', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    response_out, response_err = sub_pro.communicate()
    return response_out.strip()


########
# main #
########
if __name__ == '__main__':
    app = Flask(__name__)
    CORS(app)
    api = Api(app)
    parser = reqparse.RequestParser()
    parser.add_argument('pro_name', type=str)
    api.add_resource(CheckProAPI, '/check_pro')
    api.add_resource(CheckSupervisorAPI, '/check_supervisor')
    # api.add_resource(ManualAssignment, '/manual_assignment')
    app.run(debug=True, use_reloader=False, host=socket.gethostbyname(socket.gethostname()), port=8787)

