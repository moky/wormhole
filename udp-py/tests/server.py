#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import sys
import os
import threading
import time
from typing import Optional, Dict

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

from udp import Channel, DiscreteChannel
from udp import Connection, ConnectionDelegate
from udp import Hub, PackageHub


class ServerHub(PackageHub):

    def __init__(self, delegate: ConnectionDelegate):
        super().__init__(delegate=delegate)
        self.__connections: Dict[tuple, Connection] = {}
        self.__sockets: Dict[tuple, socket.socket] = {}

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
            conn = super().create_connection(remote=remote, local=local)
            self.__connections[local] = conn
        return conn

    # Override
    def create_channel(self, remote: Optional[tuple], local: Optional[tuple]) -> Channel:
        sock = self.__sockets.get(local)
        if sock is not None:
            return DiscreteChannel(sock=sock)
        else:
            raise LookupError('failed to get channel: %s -> %s' % (remote, local))


class Server(threading.Thread, ConnectionDelegate):

    def __init__(self, host: str, port: int):
        super().__init__()
        self.__local_address = (host, port)
        self.__hub: Optional[ServerHub] = None
        self.__running = False

    @property
    def hub(self) -> ServerHub:
        return self.__hub

    @hub.setter
    def hub(self, peer: ServerHub):
        self.__hub = peer

    # noinspection PyMethodMayBeStatic
    def info(self, msg: str):
        print('> %s' % msg)

    # noinspection PyMethodMayBeStatic
    def error(self, msg: str):
        print('ERROR> %s' % msg)

    # Override
    def connection_state_changing(self, connection: Connection, current_state, next_state):
        self.info('!!! connection (%s, %s) state changed: %s -> %s'
                  % (connection.local_address, connection.remote_address, current_state, next_state))

    # Override
    def connection_data_received(self, connection: Connection, remote: tuple, wrapper, payload: bytes):
        text = payload.decode('utf-8')
        self.info('<<< received (%d bytes) from %s: %s' % (len(payload), remote, text))
        text = '%d# %d byte(s) received' % (self.counter, len(payload))
        self.counter += 1
        self.info('>>> responding: %s' % text)
        data = text.encode('utf-8')
        self.__send(data=data, source=self.__local_address, destination=remote)

    counter = 0

    def __send(self, data: bytes, source: tuple, destination: tuple):
        try:
            self.hub.send_message(body=data, source=source, destination=destination)
        except socket.error as error:
            self.error('failed to send message: %s' % error)

    def start(self):
        self.hub.bind(local=self.__local_address)
        self.__running = True
        super().start()

    def run(self):
        while self.__running:
            self.hub.tick()
            time.sleep(0.128)


SERVER_HOST = Hub.inet_address()
SERVER_PORT = 9394


if __name__ == '__main__':

    # create server
    print('UDP server (%s:%d) starting ...' % (SERVER_HOST, SERVER_PORT))

    g_server = Server(host=SERVER_HOST, port=SERVER_PORT)

    g_server.hub = ServerHub(delegate=g_server)

    g_server.start()
