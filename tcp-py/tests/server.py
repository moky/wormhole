#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import sys
import os
import threading
import time
from typing import Set, Optional

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

from tcp import Channel, ConnectionDelegate, Connection
from tcp import StreamHub, StreamChannel

from tests.config import SERVER_HOST, SERVER_PORT


class ServerHub(StreamHub):

    def create_channel(self, remote: tuple, local: tuple) -> Channel:
        for sock in Server.slave_sockets:
            try:
                if sock.getpeername() == remote:
                    return StreamChannel(sock=sock)
            except IOError as error:
                print('ServerHub error: %s' % error)


class Server(threading.Thread, ConnectionDelegate):

    local_address: tuple = None
    master_socket: socket.socket = None
    slave_sockets: Set[socket.socket] = set()

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
            return self.hub.receive(source=source, destination=destination)
        except socket.error as error:
            print('Server error: %s' % error)

    def __send(self, data: bytes, source: tuple, destination: tuple) -> bool:
        return self.hub.send(data=data, source=source, destination=destination)

    def start(self):
        self.__running = True
        super().start()

    def run(self):
        while self.__running:
            if not self.process():
                time.sleep(2)

    def process(self) -> bool:
        sockets = set(self.slave_sockets)
        count = 0
        dying = set()
        # receive data
        for sock in sockets:
            if getattr(sock, '_closed', False):
                dying.add(sock)
                continue
            try:
                remote = sock.getpeername()
            except socket.error as error:
                print('failed to get remote address: %s' % error)
                continue
            data = self.__receive(source=remote, destination=self.local_address)
            if data is not None and len(data) > 0:
                self.received_data(data=data, source=remote, destination=self.local_address)
                count += 1
        # check closed channels
        if len(dying) > 0:
            self.info('%d channel(s) dying' % len(dying))
        for sock in dying:
            self.slave_sockets.discard(sock)
        if len(self.slave_sockets) > 0:
            self.info('%d channel(s) alive' % len(self.slave_sockets))
        return count > 0


if __name__ == '__main__':

    server_address = (SERVER_HOST, SERVER_PORT)
    print('TCP server (%s) starting ...' % str(server_address))

    # binding server socket
    g_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    g_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    g_sock.setblocking(True)
    g_sock.bind(server_address)
    g_sock.listen(1)
    # g_sock.setblocking(False)

    Server.local_address = server_address
    Server.master_socket = g_sock

    g_server = Server()
    Server.hub = ServerHub(delegate=g_server)
    g_server.start()

    while True:
        remote_socket, _ = g_sock.accept()
        if remote_socket is not None:
            Server.slave_sockets.add(remote_socket)
