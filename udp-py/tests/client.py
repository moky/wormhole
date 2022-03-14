#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import random
import time

import sys
import os
from typing import Optional

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

from udp import Connection
from udp import Docker, DockerDelegate, DockerStatus
from udp import Hub, ClientHub
from udp import Arrival, PackageArrival, Departure, PackageDeparture

from tests.stargate import UDPGate


class PacketClientHub(ClientHub):

    # Override
    def _get_connection(self, remote: tuple, local: Optional[tuple]) -> Optional[Connection]:
        return super()._get_connection(remote=remote, local=None)

    # Override
    def _set_connection(self, remote: tuple, local: Optional[tuple], connection: Connection):
        super()._set_connection(remote=remote, local=None, connection=connection)

    # Override
    def _remove_connection(self, remote: tuple, local: Optional[tuple], connection: Optional[Connection]):
        super()._remove_connection(remote=remote, local=None, connection=connection)


class Client(DockerDelegate):

    def __init__(self, local: tuple, remote: tuple):
        super().__init__()
        self.__local_address = local
        self.__remote_address = remote
        gate = UDPGate(delegate=self, daemonic=True)
        gate.hub = PacketClientHub(delegate=gate)
        self.__gate = gate

    @property
    def local_address(self) -> tuple:
        return self.__local_address

    @property
    def remote_address(self) -> tuple:
        return self.__remote_address

    @property
    def gate(self) -> UDPGate:
        return self.__gate

    @property
    def hub(self) -> ClientHub:
        return self.gate.hub

    def start(self):
        self.hub.bind(address=self.local_address)
        self.gate.start()

    def stop(self):
        self.gate.stop()

    def send(self, data: bytes):
        self.gate.send_command(body=data, remote=self.remote_address, local=self.local_address)
        self.gate.send_message(body=data, remote=self.remote_address, local=self.local_address)

    #
    #   Gate Delegate
    #

    # Override
    def docker_status_changed(self, previous: DockerStatus, current: DockerStatus, docker: Docker):
        remote = docker.remote_address
        local = docker.local_address
        UDPGate.info('!!! connection (%s, %s) state changed: %s -> %s' % (remote, local, previous, current))

    # Override
    def docker_received(self, ship: Arrival, docker: Docker):
        assert isinstance(ship, PackageArrival), 'arrival ship error: %s' % ship
        pack = ship.package
        data = pack.body.get_bytes()
        try:
            text = data.decode('utf-8')
        except UnicodeDecodeError as error:
            UDPGate.error(msg='failed to decode data: %s, %s' % (error, data))
            text = str(data)
        source = docker.remote_address
        UDPGate.info('<<< received (%d bytes) from %s: %s' % (len(data), source, text))

    # Override
    def docker_sent(self, ship: Departure, docker: Docker):
        assert isinstance(ship, PackageDeparture), 'departure ship error: %s' % ship
        size = ship.package.body.size
        UDPGate.info('message sent: %d byte(s) to %s' % (size, docker.remote_address))

    # Override
    def docker_failed(self, error: IOError, ship: Departure, docker: Docker):
        UDPGate.error('failed to sent: %s, %s' % (error, docker))

    # Override
    def docker_error(self, error: IOError, ship: Departure, docker: Docker):
        UDPGate.error('connection error: %s, %s' % (error, docker))

    def test(self):
        text = b'Hello world!' * 512
        # test send
        for i in range(16):
            data = b'%d sheep:%s' % (i, text)
            UDPGate.info('>>> sending (%d bytes): %s' % (len(data), data))
            self.send(data=data)
            time.sleep(2)
        time.sleep(60)


SERVER_HOST = Hub.inet_address()
SERVER_PORT = 9394

CLIENT_HOST = Hub.inet_address()
CLIENT_PORT = random.choice(range(9900, 9999))


if __name__ == '__main__':

    local_address = (CLIENT_HOST, CLIENT_PORT)
    server_address = (SERVER_HOST, SERVER_PORT)
    UDPGate.info('Connecting UDP server (%s -> %s) ...' % (local_address, server_address))

    g_client = Client(local=local_address, remote=server_address)

    g_client.start()
    g_client.test()
    g_client.stop()

    UDPGate.info('Terminated.')
