#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import sys
import os
import threading
import time
import weakref
from typing import Optional, Union, Dict

from udp.ba import ByteArray, Data
from udp import Channel, DiscreteChannel
from udp import Connection, ConnectionDelegate
from udp import Hub, BaseHub, BaseConnection

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

import stun

from tests.srv_cnf import *


class ServerHub(BaseHub):

    def __init__(self, delegate: ConnectionDelegate):
        super().__init__()
        self.__delegate = weakref.ref(delegate)
        self.__connections: Dict[tuple, Connection] = {}
        self.__sockets: Dict[tuple, socket.socket] = {}

    @property
    def delegate(self) -> ConnectionDelegate:
        return self.__delegate()

    def bind(self, local: tuple) -> Connection:
        sock = self.__sockets.get(local)
        if sock is None:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            sock.bind(local)
            sock.setblocking(False)
            self.__sockets[local] = sock
        return self.connect(remote=None, local=local)

    # Override
    def create_connection(self, remote: Optional[tuple], local: Optional[tuple]) -> Connection:
        conn = self.__connections.get(local)
        if conn is None:
            conn = self.__create_connection(remote=None, local=local)
            self.__connections[local] = conn
        return conn

    def __create_connection(self, remote: Optional[tuple], local: Optional[tuple]) -> Connection:
        # create connection with channel
        sock = self.create_channel(remote=remote, local=local)
        conn = BaseConnection(remote=remote, local=local, channel=sock)
        # set delegate
        if conn.delegate is None:
            conn.delegate = self.delegate
        # start FSM
        conn.start()
        return conn

    def create_channel(self, remote: Optional[tuple], local: Optional[tuple]) -> Channel:
        sock = self.__sockets.get(local)
        if sock is not None:
            return DiscreteChannel(sock=sock)
        else:
            raise LookupError('failed to get channel: %s -> %s' % (remote, local))


class Server(stun.Server, threading.Thread, ConnectionDelegate):

    def __init__(self, host: str = '0.0.0.0', port: int = 3478, change_port: int = 3479):
        super().__init__(host=host, port=port, change_port=change_port)
        self.__hub = ServerHub(delegate=self)
        self.__running = False

    # noinspection PyMethodMayBeStatic
    def info(self, msg: str):
        print('> ', msg)

    # noinspection PyMethodMayBeStatic
    def error(self, msg: str):
        print('ERROR> ', msg)

    # Override
    def connection_state_changing(self, connection: Connection, current_state, next_state):
        self.info('!!! connection (%s, %s) state changed: %s -> %s'
                  % (connection.local_address, connection.remote_address, current_state, next_state))

    # Override
    def connection_data_received(self, connection: Connection, remote: tuple, wrapper, payload: bytes):
        data = Data(buffer=payload)
        self.handle(data=data, remote_ip=remote[0], remote_port=remote[1])

    # Override
    def send(self, data: ByteArray, destination: tuple, source: Union[tuple, int] = None) -> bool:
        try:
            if source is None:
                source = self.source_address
            elif isinstance(source, int):
                source = (self.source_address[0], source)
            self.__hub.send(data=data.get_bytes(), source=source, destination=destination)
            return True
        except socket.error:
            return False

    def start(self):
        primary_address = self.source_address
        secondary_address = (self.source_address[0], self.change_port)
        self.__hub.bind(local=primary_address)
        self.__hub.bind(local=secondary_address)
        self.__running = True
        super().start()

    def stop(self):
        self.__running = False

    def run(self):
        while self.__running:
            self.__hub.tick()
            time.sleep(0.1)


# SERVER_HOST = '0.0.0.0'
SERVER_HOST = Hub.inet_address()


if __name__ == '__main__':

    print('STUN server (%s:%d, %d) starting ...' % (SERVER_HOST, SERVER_PORT, CHANGE_PORT))

    g_server = Server(host=SERVER_HOST, port=SERVER_PORT, change_port=CHANGE_PORT)

    g_server.changed_address = CHANGED_ADDRESS
    g_server.neighbour = NEIGHBOR_SERVER

    g_server.start()
