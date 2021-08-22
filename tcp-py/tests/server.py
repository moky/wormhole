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
from tcp import Hub, StreamHub, StreamChannel


class ServerHub(StreamHub):

    def create_channel(self, remote: Optional[tuple], local: Optional[tuple]) -> Channel:
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

    def connection_data_received(self, connection: Connection, remote: tuple, wrapper, payload: bytes):
        text = payload.decode('utf-8')
        self.info('<<< received (%d bytes) from %s: %s' % (len(payload), remote, text))
        text = '%d# %d byte(s) received' % (self.counter, len(payload))
        self.counter += 1
        self.info('>>> responding: %s' % text)
        data = text.encode('utf-8')
        self.__send(data=data, source=self.local_address, destination=remote)

    counter = 0

    def __send(self, data: bytes, source: Optional[tuple], destination: tuple):
        self.hub.send(data=data, source=source, destination=destination)

    def start(self):
        self.__running = True
        super().start()

    def run(self):
        while self.__running:
            self.hub.tick()
            self.__clean()
            time.sleep(0.128)

    def __clean(self):
        sockets = set(self.slave_sockets)
        dying = set()
        # receive data
        for sock in sockets:
            if getattr(sock, '_closed', False):
                dying.add(sock)
        # check closed channels
        if len(dying) > 0:
            self.info('%d channel(s) dying' % len(dying))
        for sock in dying:
            self.slave_sockets.discard(sock)
        if len(self.slave_sockets) > 0:
            self.info('%d channel(s) alive' % len(self.slave_sockets))


SERVER_HOST = Hub.inet_address()
SERVER_PORT = 9394


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
        remote_socket, remote_address = g_sock.accept()
        if remote_socket is not None:
            Server.slave_sockets.add(remote_socket)
            Server.hub.connect(remote=remote_address, local=server_address)
