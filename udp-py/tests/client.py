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

from udp.ba import ByteArray
from udp import Channel, DiscreteChannel
from udp import Connection, ConnectionDelegate
from udp import Hub, ActivePackageHub


class ClientHub(ActivePackageHub):

    def __init__(self, delegate: ConnectionDelegate):
        super().__init__(delegate=delegate)
        self.__running = False

    @property
    def running(self) -> bool:
        return self.__running

    def start(self):
        self.__running = True

    def stop(self):
        self.__running = False

    # Override
    def create_channel(self, remote: tuple, local: Optional[tuple] = None) -> Channel:
        channel = DiscreteChannel(remote=remote, local=local)
        channel.configure_blocking(False)
        return channel


class Client(ConnectionDelegate):

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

    # Override
    def connection_state_changed(self, connection: Connection, previous, current):
        self.info('!!! connection (%s, %s) state changed: %s -> %s'
                  % (connection.local_address, connection.remote_address, previous, current))

    # Override
    def connection_data_received(self, connection: Connection, remote: tuple, wrapper, payload):
        if isinstance(payload, ByteArray):
            payload = payload.get_bytes()
        text = payload.decode('utf-8')
        self.info('<<< received (%d bytes) from %s: %s' % (len(payload), remote, text))

    def __send(self, data: bytes):
        try:
            source = self.__local_address
            destination = self.__remote_address
            self.__hub.send_command(body=data, source=source, destination=destination)
            self.__hub.send_message(body=data, source=source, destination=destination)
        except Exception as error:
            self.error('failed to send data: %s' % error)

    def start(self):
        self.__hub.connect(remote=self.__remote_address, local=self.__local_address)
        self.__hub.start()
        threading.Thread(target=self.run).start()

    def stop(self):
        self.__hub.stop()

    def run(self):
        while self.__hub.running:
            self.__hub.tick()
            time.sleep(0.0078125)

    def test(self):
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


SERVER_HOST = Hub.inet_address()
SERVER_PORT = 9394

CLIENT_HOST = Hub.inet_address()
CLIENT_PORT = random.choice(range(9900, 9999))


if __name__ == '__main__':

    local_address = (CLIENT_HOST, CLIENT_PORT)
    server_address = (SERVER_HOST, SERVER_PORT)
    print('Connecting UDP server (%s->%s) ...' % (local_address, server_address))

    g_client = Client(local=local_address, remote=server_address)

    g_client.start()
    g_client.test()
    g_client.stop()
