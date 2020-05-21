#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import time
from typing import Union

import sys
import os

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

import udp


SERVER_HOST = '127.0.0.1'
SERVER_PORT = 9394

CLIENT_PORT = 9527

# create a hub for sockets
server_address = (SERVER_HOST, SERVER_PORT)
g_hub = udp.Hub()
g_hub.open(port=CLIENT_PORT)
g_hub.connect(destination=server_address)
g_hub.start()


class Client(udp.Peer, udp.PeerDelegate):

    def __init__(self):
        super().__init__()
        self.delegate = self

    #
    #   PeerDelegate
    #
    def send_data(self, data: bytes, destination: tuple, source: Union[tuple, int] = None) -> int:
        return g_hub.send(data=data, destination=destination, source=source)

    def received_command(self, cmd: bytes, source: tuple, destination: tuple) -> bool:
        print('received cmd from %s to %s: %s' % (source, destination, cmd))
        return True

    def received_message(self, msg: bytes, source: tuple, destination: tuple) -> bool:
        print('received msg from %s to %s: %s' % (source, destination, msg))
        return True


if __name__ == '__main__':
    # create client
    client = Client()
    client.start()
    g_hub.add_listener(listener=client)
    # test send
    counter = 0
    while client.running:
        counter += 2
        if counter > 32:
            break
        text = '%d sheep' % counter
        print('sending msg "%s" to %s' % (text, server_address))
        client.send_message(data=text.encode('utf-8'), destination=server_address)
        time.sleep(2)
    # exit
    client.stop()
    g_hub.stop()
