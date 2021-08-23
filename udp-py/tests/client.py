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

from udp import Channel, DiscreteChannel
from udp import Connection, ConnectionDelegate
from udp import Hub, ActivePackageHub


class ClientHub(ActivePackageHub):

    # Override
    def create_channel(self, remote: tuple, local: Optional[tuple] = None) -> Channel:
        channel = DiscreteChannel(remote=remote, local=local)
        channel.configure_blocking(False)
        return channel


class Client(threading.Thread, ConnectionDelegate):

    def __init__(self, local: tuple, remote: tuple):
        super().__init__()
        self.__local_address = local
        self.__remote_address = remote
        self.__hub: Optional[ClientHub] = None

    @property
    def hub(self) -> ClientHub:
        return self.__hub

    @hub.setter
    def hub(self, peer: ClientHub):
        self.__hub = peer

    # noinspection PyMethodMayBeStatic
    def info(self, msg: str):
        print('> %s' % msg)

    # noinspection PyMethodMayBeStatic
    def error(self, msg: str):
        print('ERROR> %s' % msg)

    def connection_state_changing(self, connection: Connection, current_state, next_state):
        self.info('!!! connection (%s, %s) state changed: %s -> %s'
                  % (connection.local_address, connection.remote_address, current_state, next_state))

    def connection_data_received(self, connection: Connection, remote: tuple, wrapper, payload: bytes):
        text = payload.decode('utf-8')
        self.info('<<< received (%d bytes) from %s: %s' % (len(payload), remote, text))

    def __send(self, data: bytes):
        try:
            source = self.__local_address
            destination = self.__remote_address
            self.hub.send_command(body=data, source=source, destination=destination)
            self.hub.send_message(body=data, source=source, destination=destination)
        except Exception as error:
            self.error('failed to send data: %s' % error)

    def __disconnect(self):
        self.hub.disconnect(remote=self.__remote_address, local=self.__local_address)

    def start(self):
        self.hub.connect(remote=self.__remote_address, local=self.__local_address)
        super().start()

    def run(self):
        text = ''
        for _ in range(1024):
            text += ' Hello!'
        # test send
        for i in range(0, 32, 2):
            data = '%d sheep:%s' % (i, text)
            data = data.encode('utf-8')
            self.info('>>> sending (%d) bytes): %s' % (len(data), data))
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
    print('Connecting UDP server (%s->%s) ...' % (local_address, server_address))

    g_client = Client(local=local_address, remote=server_address)

    g_client.hub = ClientHub(delegate=g_client)

    g_client.start()
