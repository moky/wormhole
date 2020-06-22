#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import time

import stun

import sys
import os

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

from tests.srv_cnf import *


class Server(stun.Server):

    def start(self):
        self.info('STUN server started')
        self.run_forever()

    def run_forever(self):
        while True:
            try:
                data, address = self.receive()
                if data is None:
                    time.sleep(0.1)
                    continue
                # noinspection PyTypeChecker
                self.handle(data=data, remote_ip=address[0], remote_port=address[1])
            except Exception as error:
                print('error: %s' % error)


if __name__ == '__main__':

    # SERVER_HOST = '0.0.0.0'
    SERVER_HOST = stun.get_local_ip()

    # create server
    print('UDP server (%s:%d) starting ...' % (SERVER_HOST, SERVER_PORT))
    g_server = Server(host=SERVER_HOST, port=SERVER_PORT, change_port=CHANGE_PORT)
    g_server.changed_address = CHANGED_ADDRESS
    g_server.neighbour = NEIGHBOR_SERVER
    g_server.start()
