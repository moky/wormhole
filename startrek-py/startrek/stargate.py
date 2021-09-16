# -*- coding: utf-8 -*-
#
#   Star Trek: Interstellar Transport
#
#                                Written in 2021 by Moky <albert.moky@gmail.com>
#
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

import socket
import weakref
from abc import abstractmethod
from typing import Optional, List, Set

from .types import AddressPairMap
from .net import Connection, ConnectionDelegate, ConnectionState
from .port import Docker, Gate, GateDelegate, GateStatus
from .port.gate import status_from_state


class StarGate(Gate, ConnectionDelegate):
    """
        Star Gate
        ~~~~~~~~~

        @abstract methods:
            - get_connection(remote, local)
            - create_docker(remote, local, advance_party)
            - cache_advance_party(data, source, destination, connection)
            - clear_advance_party(source, destination, connection)
    """

    def __init__(self, delegate: GateDelegate):
        super().__init__()
        self.__delegate = weakref.ref(delegate)
        self.__docker_pool: AddressPairMap[Docker] = AddressPairMap()

    @property
    def delegate(self) -> Optional[GateDelegate]:
        return self.__delegate()

    @abstractmethod  # protected
    def get_connection(self, remote: tuple, local: Optional[tuple]) -> Optional[Connection]:
        """
        Get exists connection from hub

        :param remote: remote address
        :param local:  local address
        :return exists connection
        """
        raise NotImplemented

    @abstractmethod  # protected
    def create_docker(self, remote: tuple, local: Optional[tuple], advance_party: List[bytes]) -> Optional[Docker]:
        """
        Create new docker for received data

        :param remote:        remote address
        :param local:         local address
        :param advance_party: received data
        :return docker
        """
        raise NotImplemented

    # protected
    def remove_docker(self, remote: tuple, local: Optional[tuple], docker: Optional[Docker]):
        self.__docker_pool.remove(remote=remote, local=local, value=docker)

    # protected
    def get_docker(self, remote: tuple, local: Optional[tuple], advance_party: Optional[List[bytes]] = None):
        worker = self.__docker_pool.get(remote=remote, local=local)
        if worker is None and advance_party is not None:
            # if docker not exists, create after checking data format
            worker = self.create_docker(remote=remote, local=local, advance_party=advance_party)
            if worker is not None:
                self.__docker_pool.put(remote=remote, local=local, value=worker)
        return worker

    # Override
    def gate_status(self, remote: tuple, local: Optional[tuple]) -> GateStatus:
        conn = self.get_connection(remote=remote, local=local)
        if conn is None:
            return GateStatus.ERROR
        else:
            return status_from_state(state=conn.state)

    #
    #   Processor
    #

    # Override
    def process(self):
        dockers = self.__docker_pool.values
        # 1. drive all dockers to process
        count = self.drive(dockers=dockers)
        # 2. remove retired dockers
        self.cleanup(dockers=dockers)
        return count > 0

    # protected
    # noinspection PyMethodMayBeStatic
    def drive(self, dockers: Set[Docker]) -> int:
        count = 0
        for worker in dockers:
            if worker.process():
                # it's busy
                count += 1
        return count > 0

    # protected
    def cleanup(self, dockers: Set[Docker]):
        for worker in dockers:
            remote = worker.remote_address
            local = worker.local_address
            # check connection state
            conn = self.get_connection(remote=remote, local=local)
            if conn is None:
                state = None
            else:
                state = conn.state
            if state is None or state == ConnectionState.ERROR:
                # connection lost, remove worker
                self.remove_docker(remote=remote, local=local, docker=worker)
            else:
                # clear expired tasks
                worker.purge()

    # protected
    def heartbeat(self, connection: Connection):
        remote = connection.remote_address
        local = connection.local_address
        worker = self.get_docker(remote=remote, local=local)
        if worker is not None:
            worker.heartbeat()

    #
    #   Connection Delegate
    #

    # Override
    def connection_state_changed(self, previous: ConnectionState, current: ConnectionState, connection: Connection):
        remote = connection.remote_address
        local = connection.local_address
        # heartbeat when connection expired
        if current is None or current == ConnectionState.ERROR:
            # connection lost, remove the docker for it
            self.remove_docker(remote=remote, local=local, docker=None)
        elif current == ConnectionState.EXPIRED:
            # heartbeat when connection expired
            try:
                self.heartbeat(connection=connection)
            except socket.error as error:
                print('[NET] heartbeat error: %s' % error)
        # callback when status changed
        delegate = self.delegate
        s1 = status_from_state(state=previous)
        s2 = status_from_state(state=current)
        if s1 != s2 and delegate is not None:
            delegate.gate_status_changed(previous=s1, current=s2, remote=remote, local=local, gate=self)

    # Override
    def connection_received(self, data: bytes, source: tuple, destination: Optional[tuple], connection: Connection):
        # get docker by (remote, local)
        worker = self.get_docker(remote=source, local=destination)
        if worker is not None:
            # docker exists, call docker.onReceived(data)
            worker.process_received(data=data)
            return
        # save advance party from this source address
        party = self.cache_advance_party(data=data, source=source, destination=destination, connection=connection)
        assert party is not None and len(party) > 0, 'advance party error'
        # docker not exists, check the data to decide which docker should be created
        worker = self.get_docker(remote=source, local=destination, advance_party=party)
        if worker is not None:
            # process advance parties one by one
            for item in party:
                worker.process_received(data=item)
            # remove advance party
            self.clear_advance_party(source=source, destination=destination, connection=connection)

    @abstractmethod  # protected
    def cache_advance_party(self, data: bytes, source: tuple, destination: Optional[tuple],
                            connection: Connection) -> List[bytes]:
        """
        Cache the advance party before decide which docker to use

        :param data:        received data
        :param source:      remote address
        :param destination: local address
        :param connection:  current connection
        :return all cached data
        """
        raise NotImplemented

    @abstractmethod  # protected
    def clear_advance_party(self, source: tuple, destination: Optional[tuple], connection: Connection):
        """
        Clear all advance parties after docker created

        :param source:      remote address
        :param destination: local address
        :param connection:  current connection
        """
        raise NotImplemented

    # Override
    def connection_sent(self, data: bytes, source: Optional[tuple], destination: tuple, connection: Connection):
        # ignore this event
        pass

    # Override
    def connection_error(self, error, data: Optional[bytes],
                         source: Optional[tuple], destination: Optional[tuple], connection: Connection):
        # failed to send data
        if error is not None and destination is not None:
            self.remove_docker(remote=destination, local=source, docker=None)
