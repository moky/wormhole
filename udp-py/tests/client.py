#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import random
import time

import sys
import os
from typing import Optional

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

from udp import Gate, GateDelegate, GateStatus
from udp import Hub, ClientHub
from udp import Arrival, PackageArrival, Departure, PackageDeparture

from tests.stargate import UDPGate


class Client(GateDelegate):

    def __init__(self, local: tuple, remote: tuple):
        super().__init__()
        self.__local_address = local
        self.__remote_address = remote
        gate = UDPGate(delegate=self)
        gate.hub = ClientHub(delegate=gate)
        self.__gate = gate

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
    def hub(self) -> ClientHub:
        return self.gate.hub

    def start(self):
        self.hub.bind(address=self.local_address)
        self.hub.connect(remote=self.remote_address, local=self.local_address)
        self.gate.start()

    def stop(self):
        self.gate.stop()

    def send(self, data: bytes):
        self.gate.send_command(body=data, source=self.local_address, destination=self.remote_address)
        self.gate.send_message(body=data, source=self.local_address, destination=self.remote_address)

    #
    #   Gate Delegate
    #

    # Override
    def gate_status_changed(self, gate: Gate, remote: tuple, local: Optional[tuple],
                            previous: GateStatus, current: GateStatus):
        UDPGate.info('!!! connection (%s, %s) state changed: %s -> %s' % (local, remote, previous, current))

    # Override
    def gate_received(self, gate: Gate, source: tuple, destination: Optional[tuple], ship: Arrival):
        assert isinstance(ship, PackageArrival), 'arrival ship error: %s' % ship
        pack = ship.package
        data = pack.body.get_bytes()
        text = data.decode('utf-8')
        UDPGate.info('<<< received (%d bytes) from %s: %s' % (len(data), source, text))

    # Override
    def gate_sent(self, gate: Gate, source: Optional[tuple], destination: tuple, ship: Departure):
        assert isinstance(ship, PackageDeparture), 'departure ship error: %s' % ship
        pack = ship.package
        data = pack.body.get_bytes()
        size = len(data)
        UDPGate.info('message sent: %d byte(s) to %s' % (size, destination))

    # Override
    def gate_error(self, gate: Gate, source: Optional[tuple], destination: tuple, ship: Departure, error):
        UDPGate.error('gate error (%s, %s): %s' % (source, destination, error))

    def test(self):
        text = ''
        for _ in range(1024):
            text += ' Hello!'
        # test send
        for i in range(16):
            data = '%d sheep:%s' % (i, text)
            data = data.encode('utf-8')
            UDPGate.info('>>> sending (%d bytes): %s' % (len(data), data))
            self.send(data=data)
            time.sleep(2)
        time.sleep(16)


SERVER_HOST = Hub.inet_address()
SERVER_PORT = 9394

CLIENT_HOST = Hub.inet_address()
CLIENT_PORT = random.choice(range(9900, 9999))


if __name__ == '__main__':

    local_address = (CLIENT_HOST, CLIENT_PORT)
    server_address = (SERVER_HOST, SERVER_PORT)
    print('Connecting UDP server (%s->%s) ...' % (local_address, server_address))

    g_client = Client(local=local_address, remote=server_address)

    g_client.start()
    g_client.test()
    g_client.stop()
