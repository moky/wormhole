#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import random
import socket
import threading
import time

import sys
import os
from typing import Optional

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

from udp import Hub
from udp import Channel, Connection, ConnectionDelegate
from udp import ActivePackageHub, DiscreteChannel


class ClientHub(ActivePackageHub):

    def create_channel(self, remote: tuple, local: Optional[tuple] = None) -> Channel:
        channel = DiscreteChannel(remote=remote, local=local)
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
        try:
            self.hub.send_command(body=data, source=None, destination=destination)
            self.hub.send_message(body=data, source=None, destination=destination)
        except socket.error as error:
            self.info('failed to send data: %s' % error)

    def __disconnect(self, remote: tuple, local: Optional[tuple]):
        self.hub.disconnect(remote=remote, local=local)

    def run(self):
        text = ''
        for _ in range(1024):
            text += ' Hello!'
        # test send
        for i in range(0, 32, 2):
            data = '%d sheep:%s' % (i, text)
            data = data.encode('utf-8')
            self.info('>>> sending (%d) bytes): %s' % (len(data), data))
            self.__send(data=data, destination=self.remote_address)
            time.sleep(2)


SERVER_HOST = Hub.inet_address()
SERVER_PORT = 9394

CLIENT_HOST = Hub.inet_address()
CLIENT_PORT = random.choice(range(9900, 9999))


if __name__ == '__main__':

    local_address = (CLIENT_HOST, CLIENT_PORT)
    server_address = (SERVER_HOST, SERVER_PORT)
    print('UDP client %s -> %s starting ...' % (local_address, server_address))

    # create client
    g_client = Client()

    Client.remote_address = server_address
    Client.hub = ClientHub(delegate=g_client)

    g_client.start()
