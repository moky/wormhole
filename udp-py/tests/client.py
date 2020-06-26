#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import time

import sys
import os

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

from tests.node import Node
from tests.config import SERVER_HOST, SERVER_PORT, CLIENT_HOST, CLIENT_PORT


class Client(Node):

    def __init__(self, host: str, port: int):
        super().__init__(host=host, port=port)
        self.server_address: tuple = None

    def send_cmd(self, cmd: str):
        data = cmd.encode('utf-8')
        address = self.server_address
        print('sending cmd (%d bytes): "%s" to %s' % (len(data), cmd, address))
        self.send_command(cmd=data, destination=address)

    def send_msg(self, msg: str):
        data = msg.encode('utf-8')
        address = self.server_address
        print('sending msg (%d bytes): "%s" to %s' % (len(data), msg, address))
        self.send_message(msg=data, destination=address)


if __name__ == '__main__':

    local_address = (CLIENT_HOST, CLIENT_PORT)
    server_address = (SERVER_HOST, SERVER_PORT)
    print('UDP client %s -> %s starting ...' % (local_address, server_address))

    # create client
    g_client = Client(host=CLIENT_HOST, port=CLIENT_PORT)
    g_client.server_address = server_address

    text = ''
    for i in range(1024):
        text += ' Hello!'
    # test send
    counter = 0
    while True:
        counter += 2
        if counter > 32:
            break
        g_client.send_cmd(cmd='%d sheep:%s' % (counter, text))
        g_client.send_msg(msg='%d sheep:%s' % (counter, text))
        time.sleep(2)
    # exit
    g_client.stop()
