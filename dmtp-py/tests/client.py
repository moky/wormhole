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

from udp import Hub, PackageHub, Gate, GateStatus, GateDelegate
from udp import Connection, ConnectionState
from udp import Arrival, Departure, PackageArrival, PackageDeparture

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

from dmtp import Client, Command, Message, LocationValue

from tests.manager import ContactManager, FieldValueEncoder, Session
from tests.stargate import UDPGate


SERVER_GZ1 = '134.175.87.98'
SERVER_GZ2 = '203.195.224.155'
SERVER_GZ3 = '129.204.94.164'

SERVER_HOST = Hub.inet_address()
SERVER_PORT = 9395

CLIENT_HOST = Hub.inet_address()
CLIENT_PORT = random.choice(range(9900, 9999))


class DmtpClient(Client, GateDelegate):

    def __init__(self, local: tuple, remote: tuple):
        super().__init__()
        self.__local_address = local
        self.__remote_address = remote
        gate = UDPGate(delegate=self)
        gate.hub = PackageHub(delegate=gate)
        self.__gate = gate
        self.__db: Optional[ContactManager] = None

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
    def hub(self) -> PackageHub:
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

    def start(self):
        self.hub.bind(address=self.local_address)
        self.gate.start()

    def stop(self):
        self.gate.stop()

    # Override
    def _connect(self, remote: tuple):
        try:
            self.hub.connect(remote=remote, local=self.__local_address)
        except socket.error as error:
            UDPGate.error('failed to connect to %s: %s' % (remote, error))

    #
    #   Gate Delegate
    #

    # Override
    def gate_status_changed(self, previous: GateStatus, current: GateStatus,
                            remote: tuple, local: Optional[tuple], gate: Gate):
        UDPGate.info('!!! connection (%s, %s) state changed: %s -> %s' % (remote, local, previous, current))

    # Override
    def gate_received(self, ship: Arrival,
                      source: tuple, destination: Optional[tuple], connection: Connection):
        assert isinstance(ship, PackageArrival), 'arrival ship error: %s' % ship
        pack = ship.package
        self._received(head=pack.head, body=pack.body, source=source)

    # Override
    def gate_sent(self, ship: Departure,
                  source: Optional[tuple], destination: tuple, connection: Connection):
        assert isinstance(ship, PackageDeparture), 'departure ship error: %s' % ship
        pack = ship.package
        data = pack.body.get_bytes()
        size = len(data)
        UDPGate.info('message sent: %d byte(s) to %s' % (size, destination))

    # Override
    def gate_error(self, error, ship: Departure,
                   source: Optional[tuple], destination: tuple, connection: Connection):
        UDPGate.error('gate error (%s, %s): %s' % (source, destination, error))

    # Override
    def _process_command(self, cmd: Command, source: tuple) -> bool:
        UDPGate.info('received cmd from %s:\n\t%s' % (source, cmd))
        # noinspection PyBroadException
        try:
            return super()._process_command(cmd=cmd, source=source)
        except Exception as error:
            UDPGate.error('failed to process cmd: %s, %s' % (cmd, error))
            traceback.print_exc()
            return False

    # Override
    def _process_message(self, msg: Message, source: tuple) -> bool:
        UDPGate.info('received msg from %s:\n\t%s' % (source, json.dumps(msg, cls=FieldValueEncoder)))
        # return super()._process_message(msg=msg, source=source)
        return True

    # Override
    def send_command(self, cmd: Command, destination: tuple) -> bool:
        UDPGate.info('sending cmd to %s:\n\t%s' % (destination, cmd))
        self.gate.send_command(body=cmd.get_bytes(), source=self.local_address, destination=destination)
        return True

    # Override
    def send_message(self, msg: Message, destination: tuple) -> bool:
        UDPGate.info('sending msg to %s:\n\t%s' % (destination, json.dumps(msg, cls=FieldValueEncoder)))
        self.gate.send_message(body=msg.get_bytes(), source=self.local_address, destination=destination)
        return True

    #
    #   Client actions
    #

    # Override
    def say_hello(self, destination: tuple) -> bool:
        if super().say_hello(destination=destination):
            return True
        cmd = Command.hello_command(identifier=self.identifier)
        UDPGate.info('send cmd: %s' % cmd)
        return self.send_command(cmd=cmd, destination=destination)

    def call(self, identifier: str) -> bool:
        cmd = Command.call_command(identifier=identifier)
        UDPGate.info('send cmd: %s' % cmd)
        return self.send_command(cmd=cmd, destination=self.__remote_address)

    def login(self, identifier: str):
        self.identifier = identifier
        self._connect(remote=self.__remote_address)
        self.say_hello(destination=self.__remote_address)

    def get_sessions(self, identifier: str) -> list:
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
                conn = self.hub.connect(remote=source_address, local=None)
                if conn is not None:
                    if conn.state in [ConnectionState.READY, ConnectionState.MAINTAINING, ConnectionState.EXPIRED]:
                        sessions.append(Session(location=loc, address=source_address))
                        continue
            mapped_address = loc.mapped_address
            if mapped_address is not None:
                conn = self.hub.connect(remote=mapped_address, local=None)
                if conn is not None:
                    if conn.state in [ConnectionState.READY, ConnectionState.MAINTAINING, ConnectionState.EXPIRED]:
                        sessions.append(Session(location=loc, address=mapped_address))
                        continue
        return sessions

    def send_text(self, receiver: str, msg: str) -> Optional[Message]:
        sessions = self.get_sessions(identifier=receiver)
        if len(sessions) == 0:
            UDPGate.info('user (%s) not login ...' % receiver)
            # ask the server to help building a connection
            self.call(identifier=receiver)
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
            UDPGate.info('send msg to %s:\n\t%s' % (item.address, msg))
            self.send_message(msg=msg, destination=item.address)
        return msg

    def test(self):
        time.sleep(2)
        self.login(identifier=user)
        # test send
        text = '你好 %s！' % friend
        index = 0
        while self.gate.running:
            time.sleep(5)
            print('---- [%d] ----: %s' % (index, text))
            self.send_text(receiver=friend, msg='%s (%d)' % (text, index))
            index += 1


if __name__ == '__main__':

    user = 'moky-%d' % CLIENT_PORT
    friend = 'moky'

    if len(sys.argv) == 3:
        user = sys.argv[1]
        friend = sys.argv[2]

    # create client
    local_address = (CLIENT_HOST, CLIENT_PORT)
    remote_address = (SERVER_HOST, SERVER_PORT)
    print('UDP client %s -> %s starting ...' % (local_address, remote_address))
    g_client = DmtpClient(local=local_address, remote=remote_address)

    # database for location of contacts
    g_client.database = ContactManager(hub=g_client.hub, local=local_address)
    g_client.identifier = user
    g_client.delegate = g_client.database

    g_client.start()
    g_client.test()
    g_client.stop()
