#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import random
import threading
import time

import sys
import os
from typing import Optional

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

from tcp import Channel, StreamChannel
from tcp import Connection, ConnectionDelegate
from tcp import Hub, ActiveStreamHub


class ClientHub(ActiveStreamHub):

    # Override
    def create_channel(self, remote: Optional[tuple], local: Optional[tuple]) -> Channel:
        channel = StreamChannel(remote=remote, local=local)
        channel.configure_blocking(False)
        return channel


class Client(threading.Thread, ConnectionDelegate):

    def __init__(self, local: tuple, remote: tuple):
        super().__init__()
        self.__local_address = local
        self.__remote_address = remote
        self.__hub = ClientHub(delegate=self)

    # noinspection PyMethodMayBeStatic
    def info(self, msg: str):
        print('> ', msg)

    # noinspection PyMethodMayBeStatic
    def error(self, msg: str):
        print('ERROR> ', msg)

    def connection_state_changing(self, connection: Connection, current_state, next_state):
        self.info('!!! connection (%s, %s) state changed: %s -> %s'
                  % (connection.local_address, connection.remote_address, current_state, next_state))

    def connection_data_received(self, connection: Connection, remote: tuple, wrapper, payload):
        text = payload.decode('utf-8')
        self.info('<<< received (%d bytes) from %s: %s' % (len(payload), remote, text))

    def __send(self, data: bytes):
        try:
            source = self.__local_address
            destination = self.__remote_address
            self.__hub.send(data=data, source=source, destination=destination)
        except Exception as error:
            self.error('failed to send data: %d byte(s), %s' % (len(data), error))

    def __disconnect(self):
        self.__hub.disconnect(remote=self.__remote_address, local=self.__local_address)

    def start(self):
        self.__hub.connect(remote=self.__remote_address, local=self.__local_address)
        super().start()

    def run(self):
        text = ''
        for _ in range(1024):
            text += ' Hello!'
        # test send
        for i in range(16):
            data = '%d sheep:%s' % (i, text)
            data = data.encode('utf-8')
            self.info('>>> sending (%d bytes): %s' % (len(data), data))
            self.__send(data=data)
            time.sleep(2)
        self.__disconnect()


SERVER_HOST = Hub.inet_address()
SERVER_PORT = 9394

CLIENT_HOST = Hub.inet_address()
CLIENT_PORT = random.choice(range(9900, 9999))


if __name__ == '__main__':

    local_address = (CLIENT_HOST, CLIENT_PORT)
    server_address = (SERVER_HOST, SERVER_PORT)
    print('Connecting TCP server (%s->%s) ...' % (local_address, server_address))

    g_client = Client(local=local_address, remote=server_address)

    g_client.start()
