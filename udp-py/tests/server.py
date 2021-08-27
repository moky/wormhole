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

from udp.ba import ByteArray
from udp import Channel, DiscreteChannel
from udp import Connection, ConnectionDelegate
from udp import Hub, PackageHub


class ServerHub(PackageHub):

    def __init__(self, delegate: ConnectionDelegate):
        super().__init__(delegate=delegate)
        self.__connections: Dict[tuple, Connection] = {}
        self.__sockets: Dict[tuple, socket.socket] = {}
        self.__running = False

    @property
    def running(self) -> bool:
        return self.__running

    def start(self):
        self.__running = True

    def stop(self):
        self.__running = False

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
            conn = super().create_connection(remote=None, local=local)
            self.__connections[local] = conn
        return conn

    # Override
    def create_channel(self, remote: Optional[tuple], local: Optional[tuple]) -> Channel:
        sock = self.__sockets.get(local)
        if sock is not None:
            return DiscreteChannel(sock=sock)
        else:
            raise LookupError('failed to get channel: %s -> %s' % (remote, local))


class Server(ConnectionDelegate):

    def __init__(self, host: str, port: int):
        super().__init__()
        self.__local_address = (host, port)
        self.__hub = ServerHub(delegate=self)

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
        text = '%d# %d byte(s) received' % (self.counter, len(payload))
        self.counter += 1
        self.info('>>> responding: %s' % text)
        data = text.encode('utf-8')
        self.__send(data=data, source=self.__local_address, destination=remote)

    counter = 0

    def __send(self, data: bytes, source: tuple, destination: tuple):
        try:
            self.__hub.send_message(body=data, source=source, destination=destination)
        except socket.error as error:
            self.error('failed to send message: %s' % error)

    def start(self):
        self.__hub.bind(local=self.__local_address)
        self.__hub.start()
        threading.Thread(target=self.run).start()

    def stop(self):
        self.__hub.stop()

    def run(self):
        while self.__hub.running:
            self.__hub.tick()
            time.sleep(0.0078125)


SERVER_HOST = Hub.inet_address()
SERVER_PORT = 9394


if __name__ == '__main__':

    print('UDP server (%s:%d) starting ...' % (SERVER_HOST, SERVER_PORT))

    g_server = Server(host=SERVER_HOST, port=SERVER_PORT)

    g_server.start()
