#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import random
import socket
import sys
import os
import time
import traceback
from typing import Optional

from startrek.skywalker import Runner
from startrek.net.state import StateOrder

from udp import SocketAddress
from udp import PorterDelegate, PorterStatus, Porter
from udp import Channel, BaseChannel
from udp import Connection
from udp import ClientHub
from udp import Arrival, Departure, PackageArrival, PackageDeparture

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

from dmtp import Client, Command, Message, LocationValue

from tests.utils import Log, Inet
from tests.manager import ContactManager, FieldValueEncoder, Session
from tests.contact import ContactHub
from tests.stargate import UDPGate


SERVER_GZ1 = '134.175.87.98'
SERVER_GZ2 = '203.195.224.155'
SERVER_GZ3 = '129.204.94.164'

SERVER_HOST = Inet.inet_address()
SERVER_PORT = 9395

CLIENT_HOST = Inet.inet_address()
CLIENT_PORT = random.choice(range(9900, 9999))


class DmtpClientHub(ClientHub, ContactHub):

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


class DmtpClient(Client, PorterDelegate):

    def __init__(self, local: SocketAddress, remote: SocketAddress):
        super().__init__()
        self.__local_address = local
        self.__remote_address = remote
        gate = UDPGate(delegate=self)
        gate.hub = DmtpClientHub(delegate=gate)
        self.__gate = gate
        self.__db: Optional[ContactManager] = None

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

    async def stop(self):
        await self.gate.stop()

    # Override
    async def _connect(self, remote: SocketAddress):
        try:
            await self.hub.connect(remote=remote, local=self.__local_address)
        except socket.error as error:
            Log.error('failed to connect to %s: %s' % (remote, error))

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
    async def _process_command(self, cmd: Command, source: SocketAddress) -> bool:
        Log.info('received cmd from %s:\n\t%s' % (source, cmd))
        # noinspection PyBroadException
        try:
            return await super()._process_command(cmd=cmd, source=source)
        except Exception as error:
            Log.error('failed to process cmd: %s, %s' % (cmd, error))
            traceback.print_exc()
            return False

    # Override
    async def _process_message(self, msg: Message, source: SocketAddress) -> bool:
        Log.info('received msg from %s:\n\t%s' % (source, json.dumps(msg, cls=FieldValueEncoder)))
        # return super()._process_message(msg=msg, source=source)
        return True

    # Override
    async def send_command(self, cmd: Command, destination: SocketAddress) -> bool:
        Log.info('sending cmd to %s:\n\t%s' % (destination, cmd))
        return await self.gate.send_command(body=cmd.get_bytes(), source=self.local_address, destination=destination)

    # Override
    async def send_message(self, msg: Message, destination: SocketAddress) -> bool:
        Log.info('sending msg to %s:\n\t%s' % (destination, json.dumps(msg, cls=FieldValueEncoder)))
        return await self.gate.send_message(body=msg.get_bytes(), source=self.local_address, destination=destination)

    #
    #   Client actions
    #

    # Override
    async def say_hello(self, destination: SocketAddress) -> bool:
        if await super().say_hello(destination=destination):
            return True
        cmd = Command.hello_command(identifier=self.identifier)
        Log.info('send cmd: %s' % cmd)
        return await self.send_command(cmd=cmd, destination=destination)

    async def call(self, identifier: str) -> bool:
        cmd = Command.call_command(identifier=identifier)
        Log.info('send cmd: %s' % cmd)
        return await self.send_command(cmd=cmd, destination=self.__remote_address)

    async def login(self, identifier: str):
        self.identifier = identifier
        await self._connect(remote=self.__remote_address)
        await self.say_hello(destination=self.__remote_address)

    async def get_sessions(self, identifier: str) -> list:
        """
        Get connected locations for user ID

        :param identifier: user ID
        :return: connected locations and addresses
        """
        sessions = []
        delegate = self.delegate
        assert delegate is not None, 'location delegate not set'
        locations = delegate.get_locations(identifier=identifier)
        for loc in locations:
            assert isinstance(loc, LocationValue), 'location error: %s' % loc
            source_address = loc.source_address
            if source_address is not None:
                conn = await self.hub.connect(remote=source_address, local=None)
                if conn is not None:
                    if conn.state in [StateOrder.READY, StateOrder.MAINTAINING, StateOrder.EXPIRED]:
                        sessions.append(Session(location=loc, address=source_address))
                        continue
            mapped_address = loc.mapped_address
            if mapped_address is not None:
                conn = await self.hub.connect(remote=mapped_address, local=None)
                if conn is not None:
                    if conn.state in [StateOrder.READY, StateOrder.MAINTAINING, StateOrder.EXPIRED]:
                        sessions.append(Session(location=loc, address=mapped_address))
                        continue
        return sessions

    async def send_text(self, receiver: str, msg: str) -> Optional[Message]:
        sessions = await self.get_sessions(identifier=receiver)
        if len(sessions) == 0:
            Log.info('user (%s) not login ...' % receiver)
            # ask the server to help building a connection
            await self.call(identifier=receiver)
            return None
        content = msg.encode('utf-8')
        msg = Message.new(info={
            'sender': self.identifier,
            'receiver': receiver,
            'time': int(time.time()),
            'data': content,
        })
        for item in sessions:
            assert isinstance(item, Session), 'session error: %s' % item
            Log.info('send msg to %s:\n\t%s' % (item.address, msg))
            await self.send_message(msg=msg, destination=item.address)
        return msg

    async def test(self, user: str, friend: str):
        time.sleep(2)
        await self.login(identifier=user)
        # test send
        text = '你好 %s！' % friend
        index = 0
        while self.gate.running:
            time.sleep(5)
            print('---- [%d] ----: %s' % (index, text))
            await self.send_text(receiver=friend, msg='%s (%d)' % (text, index))
            index += 1


async def main():
    user = 'moky-%d' % CLIENT_PORT
    friend = 'moky'

    if len(sys.argv) == 3:
        user = sys.argv[1]
        friend = sys.argv[2]

    # create client
    local_address = (CLIENT_HOST, CLIENT_PORT)
    remote_address = (SERVER_HOST, SERVER_PORT)
    print('DMTP client %s -> %s starting ...' % (local_address, remote_address))
    client = DmtpClient(local=local_address, remote=remote_address)

    # database for location of contacts
    client.database = ContactManager(hub=client.hub, local=local_address)
    client.identifier = user
    client.delegate = client.database

    await client.start()
    await client.test(user=user, friend=friend)
    await client.stop()


if __name__ == '__main__':
    Runner.sync_run(main=main())
