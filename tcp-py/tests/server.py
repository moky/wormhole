#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from typing import Optional

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

from tcp import Connection
from tcp import Gate, GateDelegate, GateStatus
from tcp import Hub, ServerHub
from tcp import Arrival, PlainArrival, Departure, PlainDeparture

from tests.stargate import TCPGate


class Server(GateDelegate):

    def __init__(self, host: str, port: int):
        super().__init__()
        self.__local_address = (host, port)
        gate = TCPGate(delegate=self)
        gate.hub = ServerHub(delegate=gate)
        self.__gate = gate

    @property
    def local_address(self) -> tuple:
        return self.__local_address

    @property
    def gate(self) -> TCPGate:
        return self.__gate

    @property
    def hub(self) -> ServerHub:
        return self.gate.hub

    def start(self):
        self.hub.bind(address=self.local_address)
        self.hub.start()
        self.gate.start()

    def send(self, data: bytes, destination: tuple):
        self.gate.send_data(payload=data, source=self.local_address, destination=destination)

    #
    #   Gate Delegate
    #

    # Override
    def gate_status_changed(self, previous: GateStatus, current: GateStatus,
                            remote: tuple, local: Optional[tuple], gate: Gate):
        TCPGate.info('!!! connection (%s, %s) state changed: %s -> %s' % (remote, local, previous, current))

    # Override
    def gate_received(self, ship: Arrival,
                      source: tuple, destination: Optional[tuple], connection: Connection):
        assert isinstance(ship, PlainArrival), 'arrival ship error: %s' % ship
        data = ship.package
        try:
            text = data.decode('utf-8')
        except UnicodeDecodeError as error:
            TCPGate.error(msg='failed to decode data: %s, %s' % (error, data))
            text = str(data)
        TCPGate.info('<<< received (%d bytes) from %s: %s' % (len(data), source, text))
        text = '%d# %d byte(s) received' % (self.counter, len(data))
        self.counter += 1
        TCPGate.info('>>> responding: %s' % text)
        data = text.encode('utf-8')
        self.send(data=data, destination=source)

    counter = 0

    # Override
    def gate_sent(self, ship: Departure,
                  source: Optional[tuple], destination: tuple, connection: Connection):
        assert isinstance(ship, PlainDeparture), 'departure ship error: %s' % ship
        data = ship.package
        size = len(data)
        TCPGate.info('message sent: %d byte(s) to %s' % (size, destination))

    # Override
    def gate_error(self, error: IOError, ship: Departure,
                   source: Optional[tuple], destination: tuple, connection: Connection):
        TCPGate.error('gate error (%s, %s): %s' % (source, destination, error))


SERVER_HOST = Hub.inet_address()
SERVER_PORT = 9394


if __name__ == '__main__':

    TCPGate.info('TCP server (%s:%d) starting ...' % (SERVER_HOST, SERVER_PORT))

    g_server = Server(host=SERVER_HOST, port=SERVER_PORT)

    g_server.start()
