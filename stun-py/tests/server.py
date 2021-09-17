#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import sys
import os
from typing import Optional, Union

from udp import Connection
from udp import Gate, GateDelegate, GateStatus
from udp import Hub, PackageHub, Arrival, Departure

from tcp import PlainArrival, PlainDeparture

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

from stun import Server

from tests.srv_cnf import *
from tests.stargate import UDPGate


class StunServer(Server, GateDelegate):

    def __init__(self, host: str = '0.0.0.0', port: int = 3478, change_port: int = 3479):
        super().__init__(host=host, port=port, change_port=change_port)
        gate = UDPGate(delegate=self)
        gate.hub = PackageHub(delegate=gate)
        self.__gate = gate

    @property
    def gate(self) -> UDPGate:
        return self.__gate

    @property
    def hub(self) -> PackageHub:
        return self.gate.hub

    def start(self):
        primary_address = self.source_address
        secondary_address = (self.source_address[0], self.change_port)
        self.hub.bind(address=primary_address)
        self.hub.bind(address=secondary_address)
        self.gate.start()
        self.info('STUN server started')
        self.info('source address: %s, another port: %d' % (self.source_address, self.change_port))
        self.info('changed address: %s' % str(self.changed_address))

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
        assert isinstance(ship, PlainArrival), 'arrival ship error: %s' % ship
        data = ship.package
        if not isinstance(data, bytes) or len(data) == 0:
            # should not happen
            return None
        self.handle(data=data, remote_ip=source[0], remote_port=source[1])

    # Override
    def gate_sent(self, ship: Departure,
                  source: Optional[tuple], destination: tuple, connection: Connection):
        assert isinstance(ship, PlainDeparture), 'departure ship error: %s' % ship
        data = ship.package
        size = len(data)
        UDPGate.info('message sent: %d byte(s) to %s' % (size, destination))

    # Override
    def gate_error(self, error, ship: Departure,
                   source: Optional[tuple], destination: tuple, connection: Connection):
        UDPGate.error('gate error (%s, %s): %s' % (source, destination, error))

    # Override
    def send(self, data: bytes, destination: tuple, source: Union[tuple, int] = None) -> bool:
        if source is None:
            source = self.source_address
        elif isinstance(source, int):
            source = (self.source_address[0], source)
        try:
            self.gate.send_data(payload=data, source=source, destination=destination)
            return True
        except socket.error:
            return False

    # Override
    def info(self, msg: str):
        UDPGate.info(msg=msg)


# SERVER_HOST = '0.0.0.0'
SERVER_HOST = Hub.inet_address()


if __name__ == '__main__':

    print('STUN server (%s:%d, %d) starting ...' % (SERVER_HOST, SERVER_PORT, CHANGE_PORT))

    g_server = StunServer(host=SERVER_HOST, port=SERVER_PORT, change_port=CHANGE_PORT)

    g_server.changed_address = CHANGED_ADDRESS
    g_server.neighbour = NEIGHBOR_SERVER

    g_server.start()
