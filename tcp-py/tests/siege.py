#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# ==============================================================================
# MIT License
#
# Copyright (c) 2021 Albert Moky
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ==============================================================================

"""
    Stress Testing
    ~~~~~~~~~~~~~~

"""

import multiprocessing
import threading
import time
from typing import Optional

from startrek.fsm import Runner

import sys
import os

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

from tcp import Connection
from tcp import Gate, GateDelegate, GateStatus
from tcp import Hub, ClientHub
from tcp import Arrival, PlainArrival, Departure, PlainDeparture

from tests.stargate import TCPGate


class Soldier(Runner, GateDelegate):

    def __init__(self, remote: tuple, local: Optional[tuple] = None):
        super().__init__()
        self.__remote_address = remote
        self.__local_address = local
        self.__gate = TCPGate(delegate=self, daemon=True)
        self.__time_to_retreat = time.time() + 32

    @property
    def local_address(self) -> tuple:
        return self.__local_address

    @property
    def remote_address(self) -> tuple:
        return self.__remote_address

    @property
    def gate(self) -> TCPGate:
        return self.__gate

    def start(self) -> threading.Thread:
        thr = threading.Thread(target=self.run, daemon=True)
        # thr.daemon = True
        thr.start()
        return thr

    def send(self, data: bytes) -> bool:
        return self.gate.send_data(payload=data, source=self.local_address, destination=self.remote_address)

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

    # Override
    def gate_sent(self, ship: Departure,
                  source: Optional[tuple], destination: tuple, connection: Connection):
        assert isinstance(ship, PlainDeparture), 'departure ship error: %s' % ship
        data = ship.package
        size = len(data)
        TCPGate.info('message sent: %d byte(s) to %s' % (size, destination))

    # Override
    def gate_error(self, error, ship: Departure,
                   source: Optional[tuple], destination: tuple, connection: Connection):
        TCPGate.error('gate error (%s, %s): %s' % (source, destination, error))

    @property  # Override
    def running(self) -> bool:
        if super().running:
            return time.time() < self.__time_to_retreat

    # Override
    def setup(self):
        super().setup()
        gate = self.gate
        gate.hub = ClientHub(delegate=gate)
        gate.start()

    # Override
    def finish(self):
        gate = self.gate
        gate.stop()
        super().finish()

    # Override
    def process(self) -> bool:
        data = b'Hello world!' * 100
        TCPGate.info('>>> sending to %s: (%d bytes) %s...' % (self.remote_address, len(data), data[:32]))
        self.send(data=data)
        return False  # return False to have a rest

    # Override
    def _idle(self):
        time.sleep(1)


class Sergeant:

    LANDING_POINT = 'normandy'

    UNITS = 10  # threads count

    def __init__(self, remote: tuple, local: Optional[tuple] = None):
        super().__init__()
        self.__remote_address = remote
        self.__local_address = local

    @property
    def local_address(self) -> tuple:
        return self.__local_address

    @property
    def remote_address(self) -> tuple:
        return self.__remote_address

    def run(self):
        threads = []
        for i in range(self.UNITS):
            print('**** thread starts: %s' % self)
            soldier = Soldier(remote=self.remote_address, local=self.local_address)
            thr = soldier.start()
            threads.append(thr)
            time.sleep(1)
        for thr in threads:
            thr.join()
            print('**** thread stopped: %s' % thr)

    def start(self) -> multiprocessing.Process:
        pro = multiprocessing.Process(target=self.run)
        pro.daemon = True
        pro.start()
        return pro


class Colonel(Runner):

    TROOPS = 16  # progresses count

    def __init__(self, remote: tuple, local: Optional[tuple] = None):
        super().__init__()
        self.__remote_address = remote
        self.__local_address = local

    @property
    def local_address(self) -> tuple:
        return self.__local_address

    @property
    def remote_address(self) -> tuple:
        return self.__remote_address

    def start(self):
        self.run()

    # Override
    def setup(self):
        super().setup()

    # Override
    def process(self) -> bool:
        processes = []
        for i in range(self.TROOPS):
            sergeant = Sergeant(remote=self.remote_address, local=self.local_address)
            pro = sergeant.start()
            processes.append(pro)
            time.sleep(1)
        for pro in processes:
            pro.join()
            print('**** process stopped: %s' % pro)
        # return False to have a rest
        return False

    # Override
    def _idle(self):
        print('====================================================')
        print('== All soldiers retreated, retry after 16 seconds...')
        print('====================================================')
        print('sleeping ...')
        for z in range(16):
            print('%d ..zzZZ' % z)
            time.sleep(1)
        print('wake up.')
        print('====================================================')
        print('== Attack !!!')
        print('====================================================')


Sergeant.LANDING_POINT = 'normandy'
Sergeant.UNITS = 10
Colonel.TROOPS = 10

# candidates
all_stations = [
    (Hub.inet_address(), 9394),
    ('127.0.0.1', 9394),
    ('149.129.234.145', 9394),
    ('', 0),
    ('', 0),
    ('', 0),
]
test_station = all_stations[1]


if __name__ == '__main__':
    print('**** Start testing ...')
    g_commander = Colonel(remote=test_station)
    g_commander.start()
