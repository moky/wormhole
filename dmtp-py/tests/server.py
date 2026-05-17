#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import socket
import sys
import os
import traceback
from typing import Optional

from startrek.utils import Log, Logging
from startrek.skywalker import Runner

from udp import SocketAddress
from udp import PorterDelegate, PorterStatus, Porter
from udp import Channel, BaseChannel
from udp import Connection
from udp import ServerHub
from udp import Arrival, Departure, PackageArrival, PackageDeparture

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

from dmtp import Server, Command, Message

from tests.utils import Inet
from tests.log import init_logger
from tests.manager import ContactManager, FieldValueEncoder
from tests.contact import ContactHub
from tests.stargate import UDPGate


class DmtpServerHub(ServerHub, ContactHub):

    # Override
    def _get_channel(self, remote: Optional[SocketAddress], local: Optional[SocketAddress]) -> Optional[Channel]:
        channel = super()._get_channel(remote=remote, local=local)
        if channel is None and remote is not None and local is not None:
            channel = super()._get_channel(remote=None, local=local)
        return channel

    # Override
    def _set_channel(self, channel: Channel,
                     remote: Optional[SocketAddress], local: Optional[SocketAddress]) -> Optional[Channel]:
        return super()._set_channel(channel=channel, remote=remote, local=local)

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


class DmtpServer(Server, PorterDelegate, Logging):

    def __init__(self, host: str, port: int):
        super().__init__()
        self.__local_address = (host, port)
        gate = UDPGate(delegate=self)
        gate.hub = DmtpServerHub(delegate=gate)
        self.__gate = gate
        self.__db: Optional[ContactManager] = None

    @property
    def local_address(self) -> SocketAddress:
        return self.__local_address

    @property
    def gate(self) -> UDPGate:
        return self.__gate

    @property
    def hub(self) -> ServerHub:
        return self.gate.hub

    @property
    def database(self) -> ContactManager:
        return self.__db

    @database.setter
    def database(self, db: ContactManager):
        self.__db = db

    @property
    def identifier(self) -> str:
        return self.__db.identifier

    @identifier.setter
    def identifier(self, uid: str):
        self.__db.identifier = uid

    # protected
    async def bind(self, local: SocketAddress):
        channel, sock = self.hub.bind(address=local)
        if sock is not None:
            assert isinstance(channel, BaseChannel), 'channel error: %s' % channel
            # set socket for this channel
            await channel.set_socket(sock=sock)

    async def start(self):
        await self.bind(local=self.local_address)
        await self.gate.start()
        while self.gate.running:
            await Runner.sleep(seconds=2.0)

    # Override
    async def _connect(self, remote: SocketAddress):
        try:
            await self.hub.connect(remote=remote, local=self.__local_address)
        except socket.error as error:
            self.error('failed to connect to %s: %s', remote, error)

    #
    #   Gate Delegate
    #

    # Override
    async def porter_status_changed(self, previous: PorterStatus, current: PorterStatus, porter: Porter):
        remote = porter.remote_address
        local = porter.local_address
        self.warning('!!! connection (%s, %s) state changed: %s -> %s', remote, local, previous, current)

    # Override
    async def porter_received(self, ship: Arrival, porter: Porter):
        assert isinstance(ship, PackageArrival), 'arrival ship error: %s' % ship
        pack = ship.package
        source = porter.remote_address
        await self._received(head=pack.head, body=pack.body, source=source)

    # Override
    async def porter_sent(self, ship: Departure, porter: Porter):
        assert isinstance(ship, PackageDeparture), 'departure ship error: %s' % ship
        pack = ship.package
        data = pack.body.get_bytes()
        size = len(data)
        destination = porter.remote_address
        self.info('message sent: %d byte(s) to %s', size, destination)

    # Override
    async def porter_failed(self, error: OSError, ship: Departure, porter: Porter):
        self.error('failed to send ship: %s', ship)

    # Override
    async def porter_error(self, error: OSError, ship: Departure, porter: Porter):
        source = porter.local_address
        destination = porter.remote_address
        self.error('gate error (%s, %s): %s', source, destination, error)

    # Override
    async def _process_command(self, cmd: Command, source: SocketAddress) -> bool:
        self.info('received cmd from %s:\n\t%s', source, cmd)
        # noinspection PyBroadException
        try:
            return await super()._process_command(cmd=cmd, source=source)
        except Exception as error:
            self.error('failed to process command (%s): %s', cmd, error)
            traceback.print_exc()
            return False

    # Override
    async def _process_message(self, msg: Message, source: SocketAddress) -> bool:
        self.info('received msg from %s:\n\t%s', source, json.dumps(msg, cls=FieldValueEncoder))
        # return super()._process_message(msg=msg, source=source)
        return True

    # Override
    async def send_command(self, cmd: Command, destination: SocketAddress) -> bool:
        self.info('sending cmd to %s:\n\t%s', destination, cmd)
        return await self.gate.send_command(body=cmd.get_bytes(), source=self.local_address, destination=destination)

    # Override
    async def send_message(self, msg: Message, destination: SocketAddress) -> bool:
        self.info('sending msg to %s:\n\t%s', destination, json.dumps(msg, cls=FieldValueEncoder))
        return await self.gate.send_message(body=msg.get_bytes(), source=self.local_address, destination=destination)

    #
    #   Server actions
    #

    # Override
    async def say_hello(self, destination: SocketAddress) -> bool:
        if await super().say_hello(destination=destination):
            return True
        cmd = Command.hello_command(identifier=self.identifier)
        return await self.send_command(cmd=cmd, destination=destination)


SERVER_HOST = Inet.inet_address()
SERVER_PORT = 9395


async def main():
    init_logger(name='UDP')

    Log.warning('DMTP server (%s:%d) starting ...', SERVER_HOST, SERVER_PORT)

    server = DmtpServer(host=SERVER_HOST, port=SERVER_PORT)

    # database for location of contacts
    server_address = (SERVER_HOST, SERVER_PORT)
    server.database = ContactManager(hub=server.hub, local=server_address)
    server.identifier = 'station@anywhere'
    server.delegate = server.database

    await server.start()

    Log.warning('DMTP server (%s:%d) stopped.', SERVER_HOST, SERVER_PORT)


if __name__ == '__main__':
    Runner.sync_run(main=main())
