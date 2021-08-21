#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import sys
import os
import threading
import time
from typing import Optional

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

from udp import Hub
from udp import Channel, Connection, ConnectionDelegate
from udp import DiscreteChannel, PackageHub


class ServerHub(PackageHub):

    def __init__(self, delegate: ConnectionDelegate):
        super().__init__(delegate=delegate)
        self.__connection = None

    def bind(self, local: tuple) -> Connection:
        return self.connect(remote=None, local=local)

    def create_connection(self, remote: tuple, local: Optional[tuple] = None) -> Connection:
        if self.__connection is None:
            self.__connection = super().create_connection(remote=remote, local=local)
        return self.__connection

    def create_channel(self, remote: tuple, local: Optional[tuple] = None) -> Channel:
        sock = Server.master
        if sock is not None:
            return DiscreteChannel(sock=sock)


class Server(threading.Thread, ConnectionDelegate):

    local_address = None
    remote_address = None
    master = None

    hub: ServerHub = None

    def __init__(self):
        super().__init__()
        self.__running = False

    # noinspection PyMethodMayBeStatic
    def info(self, msg: str):
        print('> %s' % msg)

    def connection_state_changing(self, connection: Connection, current_state, next_state):
        self.info('!!! connection (%s, %s) state changed: %s -> %s'
                  % (connection.local_address, connection.remote_address, current_state, next_state))

    def connection_data_received(self, connection: Connection, remote: tuple, wrapper, payload: bytes):
        text = payload.decode('utf-8')
        self.info('<<< received (%d bytes) from %s: %s' % (len(payload), remote, text))
        text = '%d# %d byte(s) received' % (self.counter, len(payload))
        self.counter += 1
        self.info('>>> responding: %s' % text)
        data = text.encode('utf-8')
        self.__send(data=data, source=self.local_address, destination=remote)

    counter = 0

    def __send(self, data: bytes, source: tuple, destination: tuple):
        try:
            self.hub.send_message(body=data, source=source, destination=destination)
        except socket.error as error:
            print('failed to send message: %s' % error)

    def start(self):
        self.__running = True
        super().start()

    def run(self):
        try:
            self.hub.bind(local=self.local_address)
        except socket.error as error:
            print('failed to connect: %s' % error)
        # running
        while self.__running:
            self.hub.tick()
            self.clean()
            time.sleep(0.1)

    def clean(self):
        pass


SERVER_HOST = Hub.inet_address()
SERVER_PORT = 9394


if __name__ == '__main__':

    # create server
    print('UDP server (%s:%d) starting ...' % (SERVER_HOST, SERVER_PORT))

    Server.local_address = (SERVER_HOST, SERVER_PORT)
    # server socket
    Server.master = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    Server.master.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    Server.master.bind(Server.local_address)
    Server.master.setblocking(False)

    g_server = Server()
    Server.hub = ServerHub(delegate=g_server)
    g_server.start()
