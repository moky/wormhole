#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import sys
import os
from typing import Optional, Union

from startrek.skywalker import Runner

from udp import SocketAddress
from udp import Channel, BaseChannel, Connection
from udp import Porter, PorterDelegate, PorterStatus
from udp import ServerHub
from udp import Arrival, Departure

from tcp import PlainArrival, PlainDeparture

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

from stun import Server

from tests.srv_cnf import *
from tests.utils import Inet, Log
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
                        remote: SocketAddress, local: Optional[SocketAddress]) -> Optional[Connection]:
        return super()._set_connection(connection=connection, remote=remote, local=None)

    # Override
    def _remove_connection(self, connection: Optional[Connection],
                           remote: SocketAddress, local: Optional[SocketAddress]) -> Optional[Connection]:
        return super()._remove_connection(connection=connection, remote=remote, local=None)


class StunServer(Server, PorterDelegate):

    def __init__(self, host: str = '0.0.0.0', port: int = 3478, change_port: int = 3479):
        super().__init__(host=host, port=port, change_port=change_port)
        gate = UDPGate(delegate=self)
        gate.hub = PacketServerHub(delegate=gate)
        self.__gate = gate

    @property
    def gate(self) -> UDPGate:
        return self.__gate

    @property
    def hub(self) -> ServerHub:
        return self.gate.hub

    # protected
    async def bind(self, local: SocketAddress):
        channel, sock = self.hub.bind(address=local)
        if sock is not None:
            assert isinstance(channel, BaseChannel), 'channel error: %s' % channel
            # set socket for this channel
            await channel.set_socket(sock=sock)

    async def start(self):
        primary_address = self.source_address
        secondary_address = (self.source_address[0], self.change_port)
        await self.bind(local=primary_address)
        await self.bind(local=secondary_address)
        await self.gate.start()
        self.info('STUN server started')
        self.info('source address: %s, another port: %d' % (self.source_address, self.change_port))
        self.info('changed address: %s' % str(self.changed_address))
        while self.gate.running:
            await Runner.sleep(seconds=2.0)

    #
    #   Gate Delegate
    #

    # Override
    async def porter_status_changed(self, previous: PorterStatus, current: PorterStatus, porter: Porter):
        remote = porter.remote_address
        local = porter.local_address
        Log.info('!!! connection (%s, %s) state changed: %s -> %s' % (remote, local, previous, current))

    # Override
    async def porter_received(self, ship: Arrival, porter: Porter):
        assert isinstance(ship, PlainArrival), 'arrival ship error: %s' % ship
        data = ship.payload
        if not isinstance(data, bytes) or len(data) == 0:
            # should not happen
            return None
        source = porter.remote_address
        await self.handle(data=data, remote_ip=source[0], remote_port=source[1])

    # Override
    async def porter_sent(self, ship: Departure, porter: Porter):
        assert isinstance(ship, PlainDeparture), 'departure ship error: %s' % ship
        data = ship.payload
        size = len(data)
        destination = porter.remote_address
        Log.info('message sent: %d byte(s) to %s' % (size, destination))

    # Override
    async def porter_failed(self, error: OSError, ship: Departure, porter: Porter):
        Log.info('failed to send ship: %s' % ship)

    # Override
    async def porter_error(self, error: OSError, ship: Departure, porter: Porter):
        source = porter.local_address
        destination = porter.remote_address
        Log.error('gate error (%s, %s): %s' % (source, destination, error))

    # Override
    async def send(self, data: bytes, destination: tuple, source: Union[tuple, int] = None) -> bool:
        if source is None:
            source = self.source_address
        elif isinstance(source, int):
            source = (self.source_address[0], source)
        try:
            # await self.hub.connect(remote=destination)
            await self.gate.send_data(payload=data, source=source, destination=destination)
            return True
        except socket.error:
            return False

    # Override
    def info(self, msg: str):
        Log.info(msg=msg)


# SERVER_HOST = '0.0.0.0'
SERVER_HOST = Inet.inet_address()


if __name__ == '__main__':

    print('STUN server (%s:%d, %d) starting ...' % (SERVER_HOST, SERVER_PORT, CHANGE_PORT))

    g_server = StunServer(host=SERVER_HOST, port=SERVER_PORT, change_port=CHANGE_PORT)

    g_server.changed_address = CHANGED_ADDRESS
    g_server.neighbour = NEIGHBOR_SERVER

    Runner.sync_run(main=g_server.start())
