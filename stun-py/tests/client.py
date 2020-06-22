#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import stun

import sys
import os

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

from tests.srv_cnf import *


# SERVER_TEST = '127.0.0.1'
SERVER_TEST = stun.get_local_ip()

STUN_SERVERS = [
    # (SERVER_TEST, 3478),
    # (SERVER_GZ1, 3478),
    # (SERVER_GZ2, 3478),
    (SERVER_HK2, 3478),
]

LOCAL_IP = stun.get_local_ip()
LOCAL_PORT = 9527


class Client(stun.Client):

    def detect(self, stun_host: str, stun_port: int):
        print('----------------------------------------------------------------')
        print('-- Detection starts from: %s ...' % stun_host)
        msg, res = self.get_nat_type(stun_host=stun_host, stun_port=stun_port)
        print('-- Detection Result:', msg)
        if res is not None:
            print('-- External Address:', res.mapped_address)
        print('----------------------------------------------------------------')


if __name__ == '__main__':

    # create client
    g_client = Client(host=LOCAL_IP, port=LOCAL_PORT)

    print('----------------------------------------------------------------')
    print('-- Local Address: (%s:%d)' % (LOCAL_IP, LOCAL_PORT))
    # create client
    for address in STUN_SERVERS:
        g_client.detect(stun_host=address[0], stun_port=address[1])
    # exit
    print('-- Local Address: (%s:%d)' % (LOCAL_IP, LOCAL_PORT))
    print('----------------------------------------------------------------')
    g_client.stop()
