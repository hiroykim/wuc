#!/usr/bin/python
# -*- coding:utf-8 -*-

"""program"""
__author__ = "MINDsLAB"
__date__ = "creation: 2018-11-27, modification: 0000-00-00"

###########
# imports #
###########
import os
import sys
import grpc
sys.path.append(os.path.join(os.getenv('MAUM_ROOT'), 'lib/python'))
from common.config import Config
from maum.brain.stt import stt_pb2, stt_pb2_grpc

###########
# options #
###########
reload(sys)
sys.setdefaultencoding("utf-8")


#########
# class #
#########
class SttClient(object):
    def __init__(self):
        self.conf = Config()
        self.conf.init('brain-stt.conf')
        self.remote = '{0}:{1}'.format(self.conf.get('brain-stt.sttd.front.export.ip'),
                                       self.conf.get('brain-stt.sttd.front.port'))
        self.channel = grpc.insecure_channel(self.remote)
        self.resolver_stub = stt_pb2_grpc.SttModelResolverStub(self.channel)

    @staticmethod
    def bytes_from_file(pcm_file_path, chunksize=10000):
        with open(pcm_file_path, "rb") as f:
            while True:
                chunk = f.read(chunksize)
                if chunk:
                    speech = stt_pb2.Speech()
                    speech.bin = chunk
                    yield speech
                else:
                    break

    def stream_recognize(self, pcm_file_path, metadata):
        stub = stt_pb2_grpc.SpeechToTextServiceStub(self.channel)
        # metadata = {(b'in.lang', b'kor'), (b'in.model', 'baseline'), (b'in.samplerate', '8000')}
        segments = stub.StreamRecognize(self.bytes_from_file(pcm_file_path), metadata=metadata)
        try:
            output_list = list()
            for seg in segments:
                # print '%.2f ~ %.2f : %s' % (seg.start / 100.0, seg.end / 100.0, seg.txt)
                # print '%.2f ~ %.2f : %s' % (seg.start / 100.0, seg.end / 100.0, seg.txt.encode('utf-8'))
                output_list.append(seg)
            return output_list
        except grpc.RpcError as e:
            # print('StreamRecognize() failed with {0}: {1}'.format(e.code(), e.details()))
            print(e)
