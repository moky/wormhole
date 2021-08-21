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

from tcp import Connection, ConnectionDelegate
from tcp import Channel, StreamChannel
from tcp import Hub, ActiveStreamHub


class ClientHub(ActiveStreamHub):

    def create_channel(self, remote: tuple, local: Optional[tuple] = None) -> Channel:
        channel = StreamChannel(remote=remote, local=local)
        channel.configure_blocking(False)
        return channel


class Client(threading.Thread, ConnectionDelegate):

    remote_address: tuple = None

    hub: ClientHub = None

    # noinspection PyMethodMayBeStatic
    def info(self, msg: str):
        print('> %s' % msg)

    def connection_state_changing(self, connection: Connection, current_state, next_state):
        self.info('!!! connection (%s, %s) state changed: %s -> %s'
                  % (connection.local_address, connection.remote_address, current_state, next_state))

    def connection_data_received(self, connection: Connection, remote: tuple, wrapper, payload: bytes):
        text = payload.decode('utf-8')
        self.info('<<< received (%d bytes) from %s: %s' % (len(payload), remote, text))

    def __send(self, data: bytes, destination: tuple):
        self.hub.send(data=data, source=None, destination=destination)

    def __disconnect(self):
        self.hub.disconnect(remote=self.remote_address, local=None)

    def run(self):
        text = ''
        for _ in range(1024):
            text += ' Hello!'
        for index in range(16):
            data = '%d sheep: %s' % (index, text)
            self.info('>>> sending (%d bytes): %s' % (len(data), data))
            data = data.encode('utf-8')
            self.__send(data=data, destination=self.remote_address)
            time.sleep(2)
        self.__disconnect()


SERVER_HOST = Hub.inet_address()
SERVER_PORT = 9394

CLIENT_HOST = Hub.inet_address()
CLIENT_PORT = random.choice(range(9900, 9999))


if __name__ == '__main__':

    server_address = (SERVER_HOST, SERVER_PORT)
    print('Connecting server (%s) ...' % str(server_address))

    g_client = Client()

    Client.remote_address = server_address
    Client.hub = ClientHub(delegate=g_client)

    g_client.start()
