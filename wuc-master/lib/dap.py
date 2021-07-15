#!/usr/bin/python
# -*- coding:utf-8 -*-

"""program"""
__author__ = "MINDsLAB"
__date__ = "creation: 2020-06-02, modification: 0000-00-00"

###########
# imports #
###########
import os
import sys
import grpc
sys.path.append(os.path.join(os.getenv('MAUM_ROOT'), 'lib/python'))
from maum.brain.dap import dap_pb2, dap_pb2_grpc

###########
# options #
###########
reload(sys)
sys.setdefaultencoding("utf-8")


#########
# class #
#########
class DiarizeClient(object):
    def __init__(self):
        self.remote = '{0}:{1}'.format('127.0.0.1', '42001')
        self.chunksize = 3145728
        self.channel = grpc.insecure_channel(self.remote)
        self.stub = dap_pb2_grpc.DiarizeStub(self.channel)

    def bytes_from_file(self, pcm_file_path):
        with open(pcm_file_path, "rb") as rf:
            wav_binary = rf.read()
            for idx in range(0, len(wav_binary), self.chunksize):
                yield dap_pb2.WavBinary(bin=wav_binary[idx:idx+self.chunksize])

    def get_diarize_from_wav(self, wav_file_path):
        segments = self.stub.GetDiarizationFromWav(self.bytes_from_file(wav_file_path)).data
        try:
            output_list = list()
            for seg in segments:
                for _ in range(40):
                    output_list.append(seg)
            return output_list
        except grpc.RpcError as e:
            # print('StreamRecognize() failed with {0}: {1}'.format(e.code(), e.details()))
            print(e)
