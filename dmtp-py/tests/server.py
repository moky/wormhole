#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import socket
import sys
import os
import traceback
from typing import Optional

from udp import Connection, Gate, GateDelegate, GateStatus
from udp import Hub, PackageHub
from udp import Arrival, Departure, PackageArrival, PackageDeparture

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

from dmtp import Server, Command, Message

from tests.manager import ContactManager, FieldValueEncoder
from tests.stargate import UDPGate


class DmtpServer(Server, GateDelegate):

    def __init__(self, host: str, port: int):
        super().__init__()
        self.__local_address = (host, port)
        gate = UDPGate(delegate=self)
        gate.hub = PackageHub(delegate=gate)
        self.__gate = gate
        self.__db: Optional[ContactManager] = None

    @property
    def local_address(self) -> tuple:
        return self.__local_address

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
            UDPGate.error('failed to process command (%s): %s' % (cmd, error))
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
    #   Server actions
    #

    # Override
    def say_hello(self, destination: tuple) -> bool:
        if super().say_hello(destination=destination):
            return True
        cmd = Command.hello_command(identifier=self.identifier)
        return self.send_command(cmd=cmd, destination=destination)


SERVER_HOST = Hub.inet_address()
SERVER_PORT = 9395


if __name__ == '__main__':

    print('UDP server (%s:%d) starting ...' % (SERVER_HOST, SERVER_PORT))

    g_server = DmtpServer(host=SERVER_HOST, port=SERVER_PORT)

    # database for location of contacts
    server_address = (SERVER_HOST, SERVER_PORT)
    g_server.database = ContactManager(hub=g_server.hub, local=server_address)
    g_server.identifier = 'station@anywhere'
    g_server.delegate = g_server.database

    g_server.start()
