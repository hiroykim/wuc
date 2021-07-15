#!/usr/bin/python
# -*- coding: utf-8 -*-

"""program"""
__author__ = "MINDsLAB"
__date__ = "creation: 2020-05-11, modification: 0000-00-00"

###########
# imports #
###########
import os
import sys
import base64
import struct
import hashlib
import argparse
import subprocess
from Crypto import Random
from Crypto.Cipher import AES

###########
# options #
###########
reload(sys)
sys.setdefaultencoding("utf-8")


#########
# class #
#########
class AESCipher(object):
    def __init__(self, conf):
        self.bs = 16
        self.conf = conf
        self.key = self.openssl_dec()
        self.salt = 'anySaltYouCanUse0f0n'
        # self.private_key = self.get_private_key(self.key, self.salt)
        self.private_key = self.key

    def _pad(self, s):
        return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)

    @staticmethod
    def _unpad(s):
        return s[0:-ord(s[-1:])]

    @staticmethod
    def get_private_key(secret_key, salt):
        return hashlib.pbkdf2_hmac('SHA256', secret_key.encode(), salt.encode(), 65536, 32)

    def encrypt(self, message):
        message = self._pad(message)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.private_key, AES.MODE_CBC, iv)
        cipher_bytes = base64.b64encode(iv + cipher.encrypt(message))
        return bytes.decode(cipher_bytes)

    def decrypt(self, encoded):
        cipher_text = base64.b64decode(encoded)
        iv = cipher_text[:AES.block_size]
        cipher = AES.new(self.private_key, AES.MODE_CBC, iv)
        plain_bytes = self._unpad(cipher.decrypt(cipher_text[self.bs:]))
        return bytes.decode(plain_bytes)

    def encrypt_file(self, in_filename, out_filename=None, chunksize=64*1024):
        if not out_filename:
            out_filename = in_filename + '.enc'
        if os.path.exists(out_filename):
            os.remove(out_filename)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.private_key, AES.MODE_CBC, iv)
        filesize = os.path.getsize(in_filename)
        with open(in_filename, 'rb') as infile:
            with open(out_filename, 'wb') as outfile:
                outfile.write(struct.pack('<Q', filesize))
                outfile.write(iv)
                while True:
                    chunk = infile.read(chunksize)
                    if len(chunk) == 0:
                        break
                    elif len(chunk) % AES.block_size != 0:
                        chunk += ' ' * (AES.block_size - len(chunk) % AES.block_size)
                    outfile.write(cipher.encrypt(chunk))

    def decrypt_file(self, in_filename, out_filename=None, chunksize=24*1024):
        if not out_filename:
            out_filename = os.path.splitext(in_filename)[0]
        if os.path.exists(out_filename):
            os.remove(out_filename)
        with open(in_filename, 'rb') as infile:
            origsize = struct.unpack('<Q', infile.read(struct.calcsize('Q')))[0]
            iv = infile.read(AES.block_size)
            cipher = AES.new(self.private_key, AES.MODE_CBC, iv)
            with open(out_filename, 'wb') as outfile:
                while True:
                    chunk = infile.read(chunksize)
                    if len(chunk) == 0:
                        break
                    outfile.write(cipher.decrypt(chunk))
                outfile.truncate(origsize)

    def is_encrypt(self, message):
        try:
            self.decrypt(message)
            return True
        except Exception:
            return False

    @staticmethod
    def sub_process(cmd):
        sub_pro = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        response_out, response_err = sub_pro.communicate()
        return response_out, response_err

    def openssl_dec(self):
        cmd = "openssl enc -seed -d -a -in {0} -pass file:{1}".format(self.conf.pd, self.conf.ps_path)
        std_out, std_err = self.sub_process(cmd)
        return std_out.strip()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-o', nargs='?', action='store', dest='option', required=True, type=str,
                        help='Input Option Ex) enc or dec or enc_file or dec_file')
    parser.add_argument('-s', nargs='?', action='store', dest='target_str', required=True, type=str,
                        help='Input Target String \ Target file path')

    class AESConfig(object):
        pd = '/srv/maum/code/cfg/.aes'
        ps_path = '/srv/maum/code/cfg/.meritz'
    arguments = parser.parse_args()
    temp = AESCipher(AESConfig)
    if arguments.option == 'enc':
        print(temp.encrypt(arguments.target_str))
    elif arguments.option == 'dec':
        print(temp.decrypt(arguments.target_str))
    elif arguments.option == 'enc_file':
        print(temp.encrypt_file(arguments.target_str))
    elif arguments.option == 'dec_file':
        print(temp.decrypt_file(arguments.target_str))
    # test_str = '안녕하세요 상담원 홍길동입니다.'
    # enc_str = temp.encrypt(test_str)
    # print(enc_str)
    # dec_str = temp.decrypt(enc_str)
    # print(dec_str)
