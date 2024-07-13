#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import random
import socket
import sys
import os
from typing import Optional

from startrek.types import SocketAddress
from startrek.skywalker import Runnable, Runner

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

from tcp import Channel, Connection
from tcp import Docker, DockerDelegate, DockerStatus
from tcp import Hub, ClientHub
from tcp import Arrival, PlainArrival, Departure, PlainDeparture

from tests.stargate import TCPGate
from tests.stargate import Log


class StreamClientHub(ClientHub):

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
        gate = TCPGate(delegate=self)
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

    async def start(self):
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
            Log.info(msg='>>> sending (%d bytes): %s' % (len(data), data))
            await self.send(data=data)
            await Runner.sleep(seconds=2)
        Log.info(msg='>>> finished.')

    async def send(self, data: bytes) -> bool:
        return await self.gate.send_message(payload=data, remote=self.remote_address, local=self.local_address)

    #
    #   Docker Delegate
    #

    # Override
    async def docker_status_changed(self, previous: DockerStatus, current: DockerStatus, docker: Docker):
        remote = docker.remote_address
        local = docker.local_address
        Log.info(msg='!!! connection (%s, %s) state changed: %s -> %s' % (remote, local, previous, current))

    # Override
    async def docker_received(self, ship: Arrival, docker: Docker):
        assert isinstance(ship, PlainArrival), 'arrival ship error: %s' % ship
        data = ship.package
        try:
            text = data.decode('utf-8')
        except UnicodeDecodeError as error:
            Log.error(msg='failed to decode data: %s, %s' % (error, data))
            text = str(data)
        source = docker.remote_address
        Log.info(msg='<<< received (%d bytes) from %s: %s' % (len(data), source, text))

    # Override
    async def docker_sent(self, ship: Departure, docker: Docker):
        assert isinstance(ship, PlainDeparture), 'departure ship error: %s' % ship
        size = len(ship.package)
        Log.info(msg='message sent: %d byte(s) to %s' % (size, docker.remote_address))

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


async def test_send(address: SocketAddress):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 0)
    sock.setblocking(True)
    sock.connect(address)
    sock.setblocking(False)
    # check
    size = sock.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF)
    Log.info(msg=' buffer size : %d' % size)
    # send
    data = b''
    for i in range(65536):
        data += b'% 8d' % i
    total = len(data)
    Log.info(msg=' total length: %d' % total)
    rest = total
    sent = 0
    while rest > 0:
        try:
            cnt = sock.send(data)
        except socket.error:
            break
        if cnt > 0:
            Log.info(msg=' sent: %d + %d' % (sent, cnt))
            sent += cnt
            rest -= cnt
            data = data[cnt:]
        else:
            break
    # sent = sock.send(data)
    Log.info(msg=' sent length : %d' % sent)
    await Runner.sleep(seconds=16)


async def test_client(local_address: SocketAddress, remote_address: SocketAddress):
    client = Client(local=local_address, remote=remote_address)
    await client.start()
    await client.run()
    await Runner.sleep(seconds=30)
    await client.stop()


async def main():
    local_address = (CLIENT_HOST, CLIENT_PORT)
    server_address = (SERVER_HOST, SERVER_PORT)
    Log.info(msg='Connecting TCP server (%s -> %s) ...' % (local_address, server_address))

    await test_client(local_address=local_address, remote_address=server_address)
    # await test_send(address=server_address)

    Log.info(msg='Terminated.')


if __name__ == '__main__':
    Runner.sync_run(main=main())
