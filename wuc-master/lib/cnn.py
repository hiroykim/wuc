#!/usr/bin/python
# -*- coding:utf-8 -*-

"""program"""
__author__ = "MINDsLAB"
__date__ = "creation: 2020-03-24, modification: 0000-00-00"

###########
# imports #
###########
import os
import sys
import grpc
import traceback
sys.path.append(os.path.join(os.getenv('MAUM_ROOT'), 'lib/python'))
from maum.brain.w2l import w2l_pb2_grpc
from maum.brain.w2l import w2l_pb2

###########
# options #
###########
reload(sys)
sys.setdefaultencoding("utf-8")


class W2lClient(object):
    def __init__(self, remote='127.0.0.1:15001', chunk_size=64*1024):
        self.channel = grpc.insecure_channel(remote)
        self.stub = w2l_pb2_grpc.SpeechToTextStub(self.channel)
        self.chunk_size = chunk_size

    def recognize(self, wav_binary):
        wav_binary = self._generate_wav_binary_iterator(wav_binary)
        return self.stub.Recognize(wav_binary)

    def _generate_wav_binary_iterator(self, wav_binary):
        for idx in range(0, len(wav_binary), self.chunk_size):
            yield w2l_pb2.Speech(bin=wav_binary[idx:idx + self.chunk_size])

    @staticmethod
    def bytes_from_file(pcm_file_path, chunksize=10000):
        with open(pcm_file_path, "rb") as f:
            while True:
                chunk = f.read(chunksize)
                if chunk:
                    speech = w2l_pb2.Speech()
                    speech.bin = chunk
                    yield speech
                else:
                    break

    def stream_recognize(self, pcm_file_path):
        segments = self.stub.StreamRecognize(self.bytes_from_file(pcm_file_path))
        try:
            output_list = list()
            for seg in segments:
                output_list.append(seg)
            return output_list
        except Exception as e:
            print(e)
            print(traceback.format_exc())
            # print('StreamReconize() failed with {0}: {1}'.format(e.code(), e.details()))


if __name__ == '__main__':
    client = W2lClient(remote='127.0.0.1:15001')
    results = client.stream_recognize('/appl/maum/samples/8k.pcm')
    for result in results:
        print('{0}\t{1}\t{2}'.format(result.start / 80.0, result.end / 80.0, result.txt.encode('utf-8')))
