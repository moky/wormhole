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

from udp.ba import Data
from udp.mtp import DataType, Package
from udp import Channel, Connection, ConnectionDelegate
from udp import DiscreteChannel, PackageConnection, PackageHub

from tests.config import SERVER_HOST, SERVER_PORT


class ServerConnection(PackageConnection):

    def receive(self, max_len: int) -> (bytes, tuple):
        data, remote = super().receive(max_len=max_len)
        if remote is not None:
            Server.remote_address = remote
        return data, remote


class ServerHub(PackageHub):

    def create_connection(self, remote: tuple, local: Optional[tuple] = None) -> Connection:
        sock = self.create_channel(remote=remote, local=local)
        conn = ServerConnection(channel=sock)
        if conn.delegate is None:
            conn.delegate = self.delegate
        conn.start()  # start FSM
        return conn

    def create_channel(self, remote: tuple, local: Optional[tuple] = None) -> Channel:
        if remote is not None:
            Server.remote_address = remote
        return Server.master_channel


class Server(threading.Thread, ConnectionDelegate):

    local_address = None
    remote_address = None
    master_channel = None

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

    def received_data(self, data: bytes, source: tuple, destination: tuple):
        text = data.decode('utf-8')
        self.info('<<< received (%d bytes) from %s to %s: %s'
                  % (len(data), source, destination, text))
        text = '%d# %d byte(s) received' % (self.counter, len(data))
        self.counter += 1
        self.info('>>> responding: %s' % text)
        data = text.encode('utf-8')
        self.__send(data=data, source=destination, destination=source)

    counter = 0

    def __receive(self, source: tuple, destination: tuple) -> bytes:
        try:
            pack = self.hub.receive_package(source=source, destination=destination)
            if pack is not None:
                return pack.body.get_bytes()
        except socket.error as error:
            print('Server error: %s' % error)

    def __send(self, data: bytes, source: tuple, destination: tuple) -> bool:
        pack = Package.new(data_type=DataType.MESSAGE, body=Data(data=data))
        return self.hub.send_package(pack=pack, source=source, destination=destination)

    def start(self):
        self.__running = True
        super().start()

    def run(self):
        while self.__running:
            if not self.process():
                time.sleep(2)

    def process(self) -> bool:
        data = self.__receive(source=self.remote_address, destination=self.local_address)
        if data is None or len(data) == 0:
            return False
        self.received_data(data=data, source=self.remote_address, destination=self.local_address)
        return True


if __name__ == '__main__':

    # create server
    print('UDP server (%s:%d) starting ...' % (SERVER_HOST, SERVER_PORT))

    Server.local_address = (SERVER_HOST, SERVER_PORT)
    # server socket
    g_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    g_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    g_sock.setblocking(True)
    # server channel
    Server.master_channel = DiscreteChannel(sock=g_sock)
    Server.master_channel.bind(host=SERVER_HOST, port=SERVER_PORT)
    Server.master_channel.configure_blocking(blocking=False)

    g_server = Server()
    Server.hub = ServerHub(delegate=g_server)
    g_server.start()
