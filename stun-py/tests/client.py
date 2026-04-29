#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import random
import socket
import sys
import os
import time
from typing import Optional, Union, Tuple

from startrek.skywalker import Runner

from udp import SocketAddress
from udp import Channel, BaseChannel
from udp import Connection
from udp import PorterDelegate, PorterStatus, Porter
from udp import ClientHub
from udp import Arrival, Departure

from tcp import PlainArrival, PlainDeparture

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

from stun import Client

from tests.utils import Inet, Log
from tests.stargate import UDPGate


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


class StunClient(Client, PorterDelegate):

    def __init__(self, host: str, port: int):
        super().__init__(host=host, port=port)
        self.__cargoes = []
        gate = UDPGate(delegate=self)
        gate.hub = PacketClientHub(delegate=gate)
        self.__gate = gate

    @property
    def gate(self) -> UDPGate:
        return self.__gate

    @property
    def hub(self) -> ClientHub:
        return self.gate.hub

    # protected
    async def bind(self, local: SocketAddress):
        channel, sock = self.hub.bind(address=local)
        if sock is not None:
            assert isinstance(channel, BaseChannel), 'channel error: %s' % channel
            # set socket for this channel
            await channel.set_socket(sock=sock)

    async def start(self):
        await self.bind(local=self.source_address)
        # await self.hub.connect(remote=self.remote_address)
        await self.gate.start()

    async def stop(self):
        await self.gate.stop()

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
        self.__cargoes.append((data, source))

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
    async def receive(self) -> Tuple[Optional[bytes], Optional[SocketAddress]]:
        data = None
        remote = None
        expired = time.time() + 2.0
        while True:
            if len(self.__cargoes) > 0:
                cargo = self.__cargoes.pop(0)
                data = cargo[0]
                remote = cargo[1]
                break
            elif time.time() > expired:
                # timeout
                break
            else:
                # time.sleep(0.25)
                await Runner.sleep(seconds=0.25)
        if data is not None:
            self.info('received %d byte(s) from %s' % (len(data), remote))
        return data, remote

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

    async def detect(self, stun_host: str, stun_port: int):
        print('----------------------------------------------------------------')
        print('-- Detection starts from:', stun_host)
        res = await self.get_nat_type(stun_host=stun_host, stun_port=stun_port)
        print('-- Detection Result:', res.get('NAT'))
        print('-- External Address:', res.get('MAPPED-ADDRESS'))
        print('----------------------------------------------------------------')


# SERVER_TEST = '127.0.0.1'
SERVER_TEST = Inet.inet_address()

STUN_SERVERS = [

    (SERVER_TEST, 3478),
    # (SERVER_GZ1, 3478),
    # (SERVER_GZ2, 3478),
    # (SERVER_HK2, 3478),

    # ("stun.xten.com", 3478),
    ("stun.voipbuster.com", 3478),
    # ("stun.sipgate.net", 3478),
    # ("stun.ekiga.net", 3478),
    # ("stun.schlund.de", 3478),
    # ("stun.voipstunt.com", 3478),  # Full Cone NAT?
    # ("stun.counterpath.com", 3478),
    # ("stun.1und1.de", 3478),
    # ("stun.gmx.net", 3478),
    # ("stun.callwithus.com", 3478),
    # ("stun.counterpath.net", 3478),
    # ("stun.internetcalls.com", 3478),
]

LOCAL_IP = Inet.inet_address()
LOCAL_PORT = random.choice(range(19900, 19999))


async def main():
    client = StunClient(host=LOCAL_IP, port=LOCAL_PORT)

    await client.start()

    print('================================================================')
    print('== Local Address: (%s:%d)' % (LOCAL_IP, LOCAL_PORT))
    # create client
    for address in STUN_SERVERS:
        await client.detect(stun_host=address[0], stun_port=address[1])
    # exit
    print('== Local Address: (%s:%d)' % (LOCAL_IP, LOCAL_PORT))
    print('================================================================')

    await client.stop()


if __name__ == '__main__':
    Runner.sync_run(main=main())
