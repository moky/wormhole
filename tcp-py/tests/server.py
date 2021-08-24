#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import sys
import os
import threading
import time
import weakref
from typing import Optional

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

from tcp import Channel, StreamChannel
from tcp import Connection, ConnectionDelegate
from tcp import Hub, StreamHub


class ServerHub(StreamHub):

    def __init__(self, delegate: ConnectionDelegate):
        super().__init__(delegate=delegate)
        self.__local_address: Optional[tuple] = None
        self.__master: Optional[socket.socket] = None
        self.__slaves = weakref.WeakValueDictionary()  # address -> socket
        self.__running = False

    @property
    def running(self) -> bool:
        return self.__running

    def bind(self, local: tuple):
        sock = self.__master
        if sock is not None:
            if not getattr(sock, '_closed', False):
                sock.close()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        sock.setblocking(True)
        sock.bind(local)
        sock.listen(1)
        # sock.setblocking(False)
        self.__master = sock
        self.__local_address = local

    def start(self):
        self.__running = True
        threading.Thread(target=self.run).start()

    def run(self):
        while self.__running:
            sock, address = self.__master.accept()
            if sock is not None:
                self.__slaves[address] = sock
                self.connect(remote=address, local=self.__local_address)

    # Override
    def create_channel(self, remote: Optional[tuple], local: Optional[tuple]) -> Channel:
        sock = self.__slaves.get(remote)
        if sock is not None:
            return StreamChannel(sock=sock)
        else:
            raise LookupError('failed to get channel: %s -> %s' % (remote, local))


class Server(threading.Thread, ConnectionDelegate):

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

    def __send(self, data: bytes, source: Optional[tuple], destination: tuple):
        try:
            self.__hub.send(data=data, source=source, destination=destination)
        except socket.error as error:
            self.error('failed to send message: %s' % error)

    def start(self):
        self.__hub.bind(local=self.__local_address)
        self.__hub.start()
        super().start()

    def run(self):
        while self.__hub.running:
            self.__hub.tick()
            # self.__clean()
            time.sleep(0.128)

    # def __clean(self):
    #     sockets = set(self.slave_sockets)
    #     dying = set()
    #     # receive data
    #     for sock in sockets:
    #         if getattr(sock, '_closed', False):
    #             dying.add(sock)
    #     # check closed channels
    #     if len(dying) > 0:
    #         self.info('%d channel(s) dying' % len(dying))
    #     for sock in dying:
    #         self.slave_sockets.discard(sock)
    #     if len(self.slave_sockets) > 0:
    #         self.info('%d channel(s) alive' % len(self.slave_sockets))


SERVER_HOST = Hub.inet_address()
SERVER_PORT = 9394


if __name__ == '__main__':

    print('TCP server (%s:%d) starting ...' % (SERVER_HOST, SERVER_PORT))

    g_server = Server(host=SERVER_HOST, port=SERVER_PORT)

    g_server.start()
