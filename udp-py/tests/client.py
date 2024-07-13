#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import random
import sys
import os
from typing import Optional

from startrek.types import SocketAddress
from startrek.skywalker import Runnable, Runner

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

from udp import Channel, Connection
from udp import Docker, DockerDelegate, DockerStatus
from udp import Hub, ClientHub
from udp import Arrival, PackageArrival, Departure, PackageDeparture

from tests.stargate import UDPGate
from tests.stargate import Log


class PacketClientHub(ClientHub):

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
                        remote: SocketAddress, local: Optional[SocketAddress]) -> Optional[Connection]:
        return super()._set_connection(connection=connection, remote=remote, local=None)

    # Override
    def _remove_connection(self, connection: Optional[Connection],
                           remote: SocketAddress, local: Optional[SocketAddress]) -> Optional[Connection]:
        return super()._remove_connection(connection=connection, remote=remote, local=None)


class Client(Runnable, DockerDelegate):

    def __init__(self, local: SocketAddress, remote: SocketAddress):
        super().__init__()
        self.__local_address = local
        self.__remote_address = remote
        gate = UDPGate(delegate=self)
        gate.hub = PacketClientHub(delegate=gate)
        self.__gate = gate

    @property
    def local_address(self) -> SocketAddress:
        return self.__local_address

    @property
    def remote_address(self) -> SocketAddress:
        return self.__remote_address

    @property
    def gate(self) -> UDPGate:
        return self.__gate

    @property
    def hub(self) -> ClientHub:
        return self.gate.hub

    async def start(self):
        await self.hub.bind(address=self.local_address)
        await self.hub.connect(remote=self.remote_address)
        await self.gate.start()

    async def stop(self):
        await self.gate.stop()

    # Override
    async def run(self):
        text = b'Hello world!' * 512
        # test send
        for i in range(16):
            data = b'%d sheep:%s' % (i, text)
            Log.info('>>> sending (%d bytes): %s' % (len(data), data))
            await self.send(data=data)
            await Runner.sleep(seconds=2)
        Log.info(msg='>>> finished.')

    async def send(self, data: bytes) -> bool:
        ok1 = await self.gate.send_command(body=data, remote=self.remote_address, local=self.local_address)
        ok2 = await self.gate.send_message(body=data, remote=self.remote_address, local=self.local_address)
        return ok1 and ok2

    #
    #   Gate Delegate
    #

    # Override
    async def docker_status_changed(self, previous: DockerStatus, current: DockerStatus, docker: Docker):
        remote = docker.remote_address
        local = docker.local_address
        Log.info('!!! connection (%s, %s) state changed: %s -> %s' % (remote, local, previous, current))

    # Override
    async def docker_received(self, ship: Arrival, docker: Docker):
        assert isinstance(ship, PackageArrival), 'arrival ship error: %s' % ship
        pack = ship.package
        data = pack.body.get_bytes()
        try:
            text = data.decode('utf-8')
        except UnicodeDecodeError as error:
            Log.error(msg='failed to decode data: %s, %s' % (error, data))
            text = str(data)
        source = docker.remote_address
        Log.info('<<< received (%d bytes) from %s: %s' % (len(data), source, text))

    # Override
    async def docker_sent(self, ship: Departure, docker: Docker):
        assert isinstance(ship, PackageDeparture), 'departure ship error: %s' % ship
        size = ship.package.body.size
        Log.info('message sent: %d byte(s) to %s' % (size, docker.remote_address))

    # Override
    async def docker_failed(self, error: IOError, ship: Departure, docker: Docker):
        Log.error('failed to sent: %s, %s' % (error, docker))

    # Override
    async def docker_error(self, error: IOError, ship: Departure, docker: Docker):
        Log.error('connection error: %s, %s' % (error, docker))


SERVER_HOST = Hub.inet_address()
SERVER_PORT = 9394

CLIENT_HOST = Hub.inet_address()
CLIENT_PORT = random.choice(range(9900, 9999))


async def test_client(local_address: SocketAddress, remote_address: SocketAddress):
    client = Client(local=local_address, remote=remote_address)
    await client.start()
    await client.run()
    await Runner.sleep(seconds=30)
    await client.stop()


async def main():
    local_address = (CLIENT_HOST, CLIENT_PORT)
    server_address = (SERVER_HOST, SERVER_PORT)
    Log.info('Connecting UDP server (%s -> %s) ...' % (local_address, server_address))

    await test_client(local_address=local_address, remote_address=server_address)

    Log.info('Terminated.')


if __name__ == '__main__':
    Runner.sync_run(main=main())
