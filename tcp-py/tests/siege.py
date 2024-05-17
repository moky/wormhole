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

from startrek.types import SocketAddress
from startrek.skywalker import Runner

import sys
import os

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

from tcp import Channel, Connection
from tcp import Docker, DockerDelegate, DockerStatus
from tcp import Hub, ClientHub
from tcp import Arrival, PlainArrival, Departure, PlainDeparture

from tests.runner import Runner as ThreadRunner
from tests.stargate import TCPGate
from tests.stargate import Log


class StreamClientHub(ClientHub):

    # Override
    def _get_channel(self, remote: Optional[SocketAddress], local: Optional[SocketAddress]) -> Optional[Channel]:
        return super()._get_channel(remote=remote, local=None)

    # Override
    def _set_channel(self, channel: Channel,
                     remote: Optional[SocketAddress], local: Optional[SocketAddress]):
        super()._set_channel(channel=channel, remote=remote, local=None)

    # Override
    def _remove_channel(self, channel: Optional[Channel],
                        remote: Optional[SocketAddress], local: Optional[SocketAddress]) -> Optional[Channel]:
        return super()._remove_channel(channel=channel, remote=remote, local=None)

    # Override
    def _get_connection(self, remote: SocketAddress, local: Optional[SocketAddress]) -> Optional[Connection]:
        return super()._get_connection(remote=remote, local=None)

    # Override
    def _set_connection(self, connection: Connection,
                        remote: SocketAddress, local: Optional[SocketAddress]):
        super()._set_connection(connection=connection, remote=remote, local=None)

    # Override
    def _remove_connection(self, connection: Optional[Connection],
                           remote: SocketAddress, local: Optional[SocketAddress]) -> Optional[Connection]:
        return super()._remove_connection(connection=connection, remote=remote, local=None)


class Soldier(ThreadRunner, DockerDelegate):

    def __init__(self, remote: SocketAddress, local: Optional[SocketAddress] = None):
        super().__init__(interval=1.0)
        self.__remote_address = remote
        self.__local_address = local
        self.__gate = TCPGate(delegate=self)
        self.__time_to_retreat = time.time() + 32

    def __str__(self) -> str:
        cname = self.__class__.__name__
        return '<%s: remote=%s, local=%s />' % (cname, self.remote_address, self.local_address)

    def __repr__(self) -> str:
        cname = self.__class__.__name__
        return '<%s: remote=%s, local=%s />' % (cname, self.remote_address, self.local_address)

    @property
    def local_address(self) -> SocketAddress:
        return self.__local_address

    @property
    def remote_address(self) -> SocketAddress:
        return self.__remote_address

    @property
    def gate(self) -> TCPGate:
        return self.__gate

    async def send(self, data: bytes) -> bool:
        return await self.gate.send_message(payload=data, remote=self.remote_address, local=self.local_address)

    #
    #   Docker Delegate
    #

    # Override
    async def docker_status_changed(self, previous: DockerStatus, current: DockerStatus, docker: Docker):
        remote = docker.remote_address
        local = docker.local_address
        Log.info(msg='!!! connection (%s, %s) state changed: %s -> %s' % (remote, local, previous, current))

    # Override
    async def docker_received(self, ship: Arrival, docker: Docker):
        assert isinstance(ship, PlainArrival), 'arrival ship error: %s' % ship
        data = ship.package
        try:
            text = data.decode('utf-8')
        except UnicodeDecodeError as error:
            Log.error(msg='failed to decode data: %s, %s' % (error, data))
            text = str(data)
        source = docker.remote_address
        Log.info(msg='<<< received (%d bytes) from %s: %s' % (len(data), source, text))

    # Override
    async def docker_sent(self, ship: Departure, docker: Docker):
        assert isinstance(ship, PlainDeparture), 'departure ship error: %s' % ship
        data = ship.package
        size = len(data)
        destination = docker.remote_address
        Log.info(msg='message sent: %d byte(s) to %s' % (size, destination))

    # Override
    async def docker_failed(self, error: IOError, ship: Departure, docker: Docker):
        Log.error('gate error: %s, %s' % (error, docker))

    # Override
    async def docker_error(self, error: IOError, ship: Departure, docker: Docker):
        Log.error('gate error: %s, %s' % (error, docker))

    #
    #   Runner
    #

    @property  # Override
    def running(self) -> bool:
        if super().running:
            return time.time() < self.__time_to_retreat

    # Override
    def start(self) -> threading.Thread:
        super().start()
        thr = threading.Thread(target=self.run, daemon=True)
        # thr.daemon = True
        thr.start()
        return thr

    # Override
    def setup(self):
        super().setup()
        gate = self.gate
        gate.hub = StreamClientHub(delegate=gate)
        Runner.async_run(coroutine=gate.start())

    # Override
    def finish(self):
        gate = self.gate
        Runner.async_run(coroutine=gate.stop())
        super().finish()

    # Override
    def process(self) -> bool:
        data = b'Hello world!' * 100
        Log.info(msg='>>> sending to %s: (%d bytes) %s...' % (self.remote_address, len(data), data[:32]))
        Runner.async_run(coroutine=self.send(data=data))
        return False  # return False to have a rest


class Sergeant:

    LANDING_POINT = 'normandy'

    UNITS = 10  # threads count

    def __init__(self, remote: SocketAddress, local: Optional[SocketAddress] = None):
        super().__init__()
        self.__remote_address = remote
        self.__local_address = local

    def __str__(self) -> str:
        cname = self.__class__.__name__
        return '<%s: remote=%s, local=%s />' % (cname, self.remote_address, self.local_address)

    def __repr__(self) -> str:
        cname = self.__class__.__name__
        return '<%s: remote=%s, local=%s />' % (cname, self.remote_address, self.local_address)

    @property
    def local_address(self) -> SocketAddress:
        return self.__local_address

    @property
    def remote_address(self) -> SocketAddress:
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


class Colonel(ThreadRunner):

    TROOPS = 16  # progresses count

    def __init__(self, remote: SocketAddress, local: Optional[SocketAddress] = None):
        super().__init__(interval=1.0)
        self.__remote_address = remote
        self.__local_address = local

    def __str__(self) -> str:
        cname = self.__class__.__name__
        return '<%s: remote=%s, local=%s />' % (cname, self.remote_address, self.local_address)

    def __repr__(self) -> str:
        cname = self.__class__.__name__
        return '<%s: remote=%s, local=%s />' % (cname, self.remote_address, self.local_address)

    @property
    def local_address(self) -> SocketAddress:
        return self.__local_address

    @property
    def remote_address(self) -> SocketAddress:
        return self.__remote_address

    # Override
    def start(self):
        super().start()
        self.run()

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
            time.sleep(self.interval)
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
