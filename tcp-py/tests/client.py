#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import random
import socket
import time

import sys
import os
from typing import Optional

from startrek.types import SocketAddress

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

from tcp import Connection
from tcp import Docker, DockerDelegate, DockerStatus
from tcp import Hub, ClientHub
from tcp import Arrival, PlainArrival, Departure, PlainDeparture

from tests.stargate import TCPGate


class StreamClientHub(ClientHub):

    # Override
    def _get_connection(self, remote: SocketAddress, local: Optional[SocketAddress]) -> Optional[Connection]:
        return super()._get_connection(remote=remote, local=None)

    # Override
    def _set_connection(self, remote: SocketAddress, local: Optional[SocketAddress], connection: Connection):
        super()._set_connection(remote=remote, local=None, connection=connection)

    # Override
    def _remove_connection(self, remote: SocketAddress, local: Optional[SocketAddress], connection: Optional[Connection]):
        super()._remove_connection(remote=remote, local=None, connection=connection)


class Client(DockerDelegate):

    def __init__(self, local: SocketAddress, remote: SocketAddress):
        super().__init__()
        self.__local_address = local
        self.__remote_address = remote
        gate = TCPGate(delegate=self, daemonic=True)
        gate.hub = StreamClientHub(delegate=gate)
        self.__gate = gate

    @property
    def local_address(self) -> SocketAddress:
        return self.__local_address

    @property
    def remote_address(self) -> SocketAddress:
        return self.__remote_address

    @property
    def gate(self) -> TCPGate:
        return self.__gate

    @property
    def hub(self) -> ClientHub:
        return self.gate.hub

    def start(self):
        self.hub.connect(remote=self.remote_address)
        self.gate.start()

    def stop(self):
        self.gate.stop()

    def send(self, data: bytes) -> bool:
        return self.gate.send_message(payload=data, remote=self.remote_address, local=self.local_address)

    #
    #   Docker Delegate
    #

    # Override
    def docker_status_changed(self, previous: DockerStatus, current: DockerStatus, docker: Docker):
        remote = docker.remote_address
        local = docker.local_address
        TCPGate.info('!!! connection (%s, %s) state changed: %s -> %s' % (remote, local, previous, current))

    # Override
    def docker_received(self, ship: Arrival, docker: Docker):
        assert isinstance(ship, PlainArrival), 'arrival ship error: %s' % ship
        data = ship.package
        try:
            text = data.decode('utf-8')
        except UnicodeDecodeError as error:
            TCPGate.error(msg='failed to decode data: %s, %s' % (error, data))
            text = str(data)
        source = docker.remote_address
        TCPGate.info('<<< received (%d bytes) from %s: %s' % (len(data), source, text))

    # Override
    def docker_sent(self, ship: Departure, docker: Docker):
        assert isinstance(ship, PlainDeparture), 'departure ship error: %s' % ship
        size = len(ship.package)
        TCPGate.info('message sent: %d byte(s) to %s' % (size, docker.remote_address))

    # Override
    def docker_failed(self, error: IOError, ship: Departure, docker: Docker):
        TCPGate.error('failed to sent: %s, %s' % (error, docker))

    # Override
    def docker_error(self, error: IOError, ship: Departure, docker: Docker):
        TCPGate.error('connection error: %s, %s' % (error, docker))

    def test(self):
        text = b'Hello world!' * 512
        # test send
        for i in range(16):
            data = b'%d sheep:%s' % (i, text)
            TCPGate.info('>>> sending (%d bytes): %s' % (len(data), data))
            self.send(data=data)
            time.sleep(2)
        time.sleep(60)


SERVER_HOST = Hub.inet_address()
SERVER_PORT = 9394

CLIENT_HOST = Hub.inet_address()
CLIENT_PORT = random.choice(range(9900, 9999))


def test_send(address: SocketAddress):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 0)
    sock.setblocking(True)
    sock.connect(address)
    sock.setblocking(False)
    # check
    size = sock.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF)
    print('[TCP] buffer size : %d' % size)
    # send
    data = b''
    for i in range(65536):
        data += b'% 8d' % i
    total = len(data)
    print('[TCP] total length: %d' % total)
    rest = total
    sent = 0
    while rest > 0:
        try:
            cnt = sock.send(data)
        except socket.error:
            break
        if cnt > 0:
            print('[TCP] sent: %d + %d' % (sent, cnt))
            sent += cnt
            rest -= cnt
            data = data[cnt:]
        else:
            break
    # sent = sock.send(data)
    print('[TCP] sent length : %d' % sent)


if __name__ == '__main__':

    local_address = (CLIENT_HOST, CLIENT_PORT)
    server_address = (SERVER_HOST, SERVER_PORT)
    TCPGate.info('Connecting TCP server (%s -> %s) ...' % (local_address, server_address))

    g_client = Client(local=local_address, remote=server_address)

    g_client.start()
    g_client.test()
    g_client.stop()

    # test_send(address=server_address)

    TCPGate.info('Terminated.')
