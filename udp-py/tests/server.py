#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from typing import Optional

from startrek.types import SocketAddress

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

from udp import Channel, Connection
from udp import Docker, DockerDelegate, DockerStatus
from udp import Hub, ServerHub
from udp import Arrival, PackageArrival, Departure, PackageDeparture

from tests.stargate import UDPGate


class PacketServerHub(ServerHub):

    # Override
    def _get_channel(self, remote: Optional[SocketAddress], local: Optional[SocketAddress]) -> Optional[Channel]:
        channel = super()._get_channel(remote=remote, local=local)
        if channel is None and remote is not None and local is not None:
            channel = super()._get_channel(remote=None, local=local)
        return channel

    # Override
    def _set_channel(self, channel: Channel,
                     remote: Optional[SocketAddress], local: Optional[SocketAddress]):
        super()._set_channel(channel=channel, remote=remote, local=local)

    # Override
    def _remove_channel(self, channel: Optional[Channel],
                        remote: Optional[SocketAddress], local: Optional[SocketAddress]) -> Optional[Channel]:
        return super()._remove_channel(channel=channel, remote=remote, local=local)

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
        gate = UDPGate(delegate=self, daemonic=False)
        gate.hub = PacketServerHub(delegate=gate)
        self.__gate = gate

    @property
    def local_address(self) -> SocketAddress:
        return self.__local_address

    @property
    def gate(self) -> UDPGate:
        return self.__gate

    @property
    def hub(self) -> ServerHub:
        return self.gate.hub

    def start(self):
        self.hub.bind(address=self.local_address)
        self.gate.start()

    def send(self, data: bytes, destination: SocketAddress):
        self.gate.send_command(body=data, remote=destination, local=self.local_address)

    #
    #   Docker Delegate
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
        text = '%d# %d byte(s) received' % (self.counter, len(data))
        self.counter += 1
        UDPGate.info('>>> responding: %s' % text)
        data = text.encode('utf-8')
        self.send(data=data, destination=source)

    counter = 0

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


SERVER_HOST = Hub.inet_address()
# SERVER_HOST = '0.0.0.0'
SERVER_PORT = 9394


if __name__ == '__main__':

    UDPGate.info('UDP server (%s:%d) starting ...' % (SERVER_HOST, SERVER_PORT))

    g_server = Server(host=SERVER_HOST, port=SERVER_PORT)

    g_server.start()
