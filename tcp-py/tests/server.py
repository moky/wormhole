#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import sys
import os
import time
from typing import Optional

from startrek.net.channel import is_closed
from startrek.types import SocketAddress

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

from tcp import Channel, Connection
from tcp import Docker, DockerDelegate, DockerStatus
from tcp import Hub, ServerHub
from tcp import Arrival, PlainArrival, Departure, PlainDeparture

from tests.stargate import TCPGate


class StreamServerHub(ServerHub):

    # Override
    def _get_channel(self, remote: Optional[SocketAddress], local: Optional[SocketAddress]) -> Optional[Channel]:
        return super()._get_channel(remote=remote, local=None)

    # Override
    def _set_channel(self, channel: Channel,
                     remote: Optional[SocketAddress], local: Optional[SocketAddress]):
        super()._set_channel(channel=channel, remote=remote, local=None)

    # Override
    def _remove_channel(self, channel: Optional[Channel],
                        remote: Optional[SocketAddress], local: Optional[SocketAddress]) -> Optional[Channel]:
        return super()._remove_channel(channel=channel, remote=remote, local=None)

    # Override
    def _get_connection(self, remote: SocketAddress, local: Optional[SocketAddress]) -> Optional[Connection]:
        return super()._get_connection(remote=remote, local=None)

    # Override
    def _set_connection(self, connection: Connection,
                        remote: SocketAddress, local: Optional[SocketAddress]):
        super()._set_connection(connection=connection, remote=remote, local=None)

    # Override
    def _remove_connection(self, connection: Optional[Connection],
                           remote: SocketAddress, local: Optional[SocketAddress]) -> Optional[Connection]:
        return super()._remove_connection(connection=connection, remote=remote, local=None)


class Server(DockerDelegate):

    def __init__(self, host: str, port: int):
        super().__init__()
        self.__local_address = (host, port)
        gate = TCPGate(delegate=self, daemonic=False)
        gate.hub = StreamServerHub(delegate=gate)
        self.__gate = gate

    @property
    def local_address(self) -> SocketAddress:
        return self.__local_address

    @property
    def gate(self) -> TCPGate:
        return self.__gate

    @property
    def hub(self) -> ServerHub:
        return self.gate.hub

    def start(self):
        self.hub.bind(address=self.local_address)
        self.hub.start()
        self.gate.start()

    def send(self, data: bytes, destination: SocketAddress) -> bool:
        return self.gate.send_message(payload=data, remote=destination, local=self.local_address)

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
        text = '%d# %d byte(s) received' % (self.counter, len(data))
        self.counter += 1
        TCPGate.info('>>> responding: %s' % text)
        data = text.encode('utf-8')
        self.send(data=data, destination=source)

    counter = 0

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


SERVER_HOST = Hub.inet_address()
# SERVER_HOST = '0.0.0.0'
SERVER_PORT = 9394


def test_receive(address: SocketAddress):
    master = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    master.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    master.setblocking(True)
    master.bind(address)
    master.listen(1)
    while True:
        try:
            sock, address = master.accept()
            time.sleep(5)
            # check
            size = sock.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)
            print('[TCP] receive buffer size1: %d' % size)
            total = 0
            while not is_closed(sock=sock):
                data = sock.recv(1024)
                cnt = len(data)
                if cnt > 0:
                    print('[TCP] received %d bytes: %s' % (cnt, data))
                    total += cnt
                else:
                    print('[TCP] closed: %s' % str(address))
                    break
            print('[TCP] total length: %d' % total)
            size = sock.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)
            print('[TCP] receive buffer size2: %d' % size)
        except socket.error as error:
            print('[TCP] socket error: %s' % error)
        except Exception as error:
            print('[TCP] accept error: %s' % error)


if __name__ == '__main__':

    TCPGate.info('TCP server (%s:%d) starting ...' % (SERVER_HOST, SERVER_PORT))

    g_server = Server(host=SERVER_HOST, port=SERVER_PORT)

    g_server.start()

    # test_receive(address=(SERVER_HOST, SERVER_PORT))
