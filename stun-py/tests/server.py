#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import sys
import os
import threading
import time
import weakref
from typing import Optional, Union

from udp.ba import Data
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
        # server connections
        self.__primary_connection = None
        self.__secondary_connection = None

    @property
    def delegate(self) -> ConnectionDelegate:
        return self.__delegate()

    def bind(self, local: tuple) -> Connection:
        return self.connect(remote=None, local=local)

    def create_connection(self, remote: Optional[tuple], local: Optional[tuple]) -> Connection:
        port = local[1]
        if port == SERVER_PORT:
            if self.__primary_connection is None:
                self.__primary_connection = self.create_server_connection(remote=remote, local=local)
            return self.__primary_connection
        elif port == CHANGE_PORT:
            if self.__secondary_connection is None:
                self.__secondary_connection = self.create_server_connection(remote=remote, local=local)
            return self.__secondary_connection
        else:
            raise ConnectionError('port not defined: %d' % port)

    def create_server_connection(self, remote: Optional[tuple], local: Optional[tuple]) -> Connection:
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
        port = local[1]
        if port == SERVER_PORT:
            return DiscreteChannel(sock=Server.primary_socket)
        elif port == CHANGE_PORT:
            return DiscreteChannel(sock=Server.secondary_socket)
        else:
            raise ConnectionError('port not defined: %d' % port)


class Server(stun.Server, threading.Thread, ConnectionDelegate):

    primary_address: tuple = None
    primary_socket: socket = None

    secondary_address: tuple = None
    secondary_socket: socket = None

    hub: ServerHub = None

    def __init__(self, host: str = '0.0.0.0', port: int = 3478, change_port: int = 3479):
        super().__init__(host=host, port=port, change_port=change_port)
        self.__running = False

    # noinspection PyMethodMayBeStatic
    def info(self, msg: str):
        print('> %s' % msg)

    def connection_state_changing(self, connection: Connection, current_state, next_state):
        self.info('!!! connection (%s, %s) state changed: %s -> %s'
                  % (connection.local_address, connection.remote_address, current_state, next_state))

    def connection_data_received(self, connection: Connection, remote: tuple, wrapper, payload: bytes):
        data = Data(buffer=payload)
        self.handle(data=data, remote_ip=remote[0], remote_port=remote[1])

    def send(self, data: Data, destination: tuple, source: Union[tuple, int] = None) -> bool:
        try:
            if source is None:
                source = self.source_address
            elif isinstance(source, int):
                source = (self.source_address[0], source)
            self.hub.send(data=data.get_bytes(), source=source, destination=destination)
            return True
        except socket.error:
            return False

    def start(self):
        self.__running = True
        super().start()
        self.info('STUN server started')

    def stop(self):
        self.__running = False

    def run(self):
        try:
            self.hub.bind(local=self.primary_address)
            self.hub.bind(local=self.secondary_address)
        except socket.error as error:
            print('failed to connect: %s' % error)
        # running
        while self.__running:
            self.hub.tick()
            self.clean()
            time.sleep(0.1)

    def clean(self):
        pass


if __name__ == '__main__':

    # SERVER_HOST = '0.0.0.0'
    SERVER_HOST = Hub.inet_address()

    Server.primary_address = (SERVER_HOST, SERVER_PORT)
    Server.secondary_address = (SERVER_HOST, CHANGE_PORT)

    # create server
    print('UDP server (%s, %s) starting ...' % (Server.primary_address, Server.secondary_address))

    # server sockets
    Server.primary_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    Server.primary_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    Server.primary_socket.bind(Server.primary_address)
    Server.primary_socket.setblocking(False)
    Server.secondary_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    Server.secondary_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    Server.secondary_socket.bind(Server.secondary_address)
    Server.secondary_socket.setblocking(False)

    g_server = Server(host=SERVER_HOST, port=SERVER_PORT, change_port=CHANGE_PORT)
    g_server.changed_address = CHANGED_ADDRESS
    g_server.neighbour = NEIGHBOR_SERVER

    Server.hub = ServerHub(delegate=g_server)

    g_server.start()
