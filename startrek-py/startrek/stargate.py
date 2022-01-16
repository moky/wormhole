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

import traceback
import weakref
from abc import abstractmethod
from typing import Optional, List, Set

from .types import Address, AddressPairMap
from .net import Connection, ConnectionDelegate, ConnectionState
from .port import Docker, Gate, GateDelegate, GateStatus
from .port.gate import status_from_state


class DockerPool(AddressPairMap[Docker]):

    # noinspection PyMethodMayBeStatic
    def _close_docker(self, docker: Docker):
        if docker.alive:
            docker.close()

    # Override
    def set(self, remote: Optional[Address], local: Optional[Address], item: Optional[Docker]):
        old = self.get(remote=remote, local=local)
        if old is not None and old is not item:
            self._close_docker(docker=old)
        super().set(remote=remote, local=local, item=item)

    # Override
    def remove(self, remote: Optional[Address], local: Optional[Address], item: Optional[Docker]) -> Optional[Docker]:
        cached = super().remove(remote=remote, local=local, item=item)
        if cached is not None:
            self._close_docker(docker=cached)
            return cached


class StarGate(Gate, ConnectionDelegate):
    """
        Star Gate
        ~~~~~~~~~

        @abstract methods:
            - get_connection(remote, local)
            - connection_error(error, data, source, destination, connection)
            - _create_docker(remote, local, advance_party)
            - _cache_advance_party(data, source, destination, connection)
            - _clear_advance_party(source, destination, connection)
    """

    def __init__(self, delegate: GateDelegate):
        super().__init__()
        self.__delegate = weakref.ref(delegate)
        self.__docker_pool = DockerPool()

    @property  # Override
    def delegate(self) -> Optional[GateDelegate]:
        return self.__delegate()

    @abstractmethod
    def _create_docker(self, remote: Address, local: Optional[Address], advance_party: List[bytes]) -> Optional[Docker]:
        """
        create new docker for received data

        :param remote:        remote address
        :param local:         local address
        :param advance_party: received data
        :return docker
        """
        raise NotImplemented

    def _all_dockers(self) -> Set[Docker]:
        """ get a copy of dockers """
        return self.__docker_pool.items

    def _get_docker(self, remote: Address, local: Optional[Address]) -> Optional[Docker]:
        """ get cached docker """
        return self.__docker_pool.get(remote=remote, local=local)

    def _set_docker(self, docker: Docker):
        """ cache docker """
        self.__docker_pool.set(remote=docker.remote_address, local=docker.local_address, item=docker)

    def _remove_docker(self, docker: Docker):
        """ remove cached docker """
        self.__docker_pool.remove(remote=docker.remote_address, local=docker.local_address, item=docker)

    # noinspection PyMethodMayBeStatic
    def _close_docker(self, docker: Docker):
        if docker.alive:
            docker.close()

    # Override
    def gate_status(self, remote: Address, local: Optional[Address]) -> GateStatus:
        conn = self.get_connection(remote=remote, local=local)
        if conn is None:
            return GateStatus.ERROR
        else:
            return status_from_state(state=conn.state)

    #
    #   Processor
    #

    # Override
    def process(self) -> bool:
        try:
            dockers = self._all_dockers()
            # 1. drive all dockers to process
            count = self._drive_dockers(dockers=dockers)
            # 2. cleanup for dockers
            self._cleanup_dockers(dockers=dockers)
            return count > 0
        except Exception as error:
            print('[NET] gate process error: %s' % error)
            traceback.print_exc()

    def _drive_dockers(self, dockers: Set[Docker]) -> int:
        count = 0
        for worker in dockers:
            try:
                if worker.alive and worker.process():
                    count += 1  # it's busy
            except Exception as error:
                print('[NET] drive docker error: %s, %s, %s' % (error, worker, self))
                traceback.print_exc()
        return count

    def _cleanup_dockers(self, dockers: Set[Docker]):
        for worker in dockers:
            if worker.alive:
                # clear expired tasks
                worker.purge()
            else:
                # remove docker which connection lost
                self._remove_docker(docker=worker)

    def _heartbeat(self, connection: Connection):
        remote = connection.remote_address
        local = connection.local_address
        docker = self._get_docker(remote=remote, local=local)
        if docker is not None:
            docker.heartbeat()

    #
    #   Connection Delegate
    #

    # Override
    def connection_state_changed(self, previous: ConnectionState, current: ConnectionState, connection: Connection):
        # 1. callback when status changed
        delegate = self.delegate
        s1 = status_from_state(state=previous)
        s2 = status_from_state(state=current)
        if s1 != s2 and delegate is not None:
            remote = connection.remote_address
            local = connection.local_address
            delegate.gate_status_changed(previous=s1, current=s2, remote=remote, local=local, gate=self)
        # 2. heartbeat when connection expired
        if current == ConnectionState.EXPIRED:
            self._heartbeat(connection=connection)

    # Override
    def connection_received(self, data: bytes, source: Address, destination: Optional[Address], connection: Connection):
        # get docker by (remote, local)
        docker = self._get_docker(remote=source, local=destination)
        if docker is not None:
            # docker exists, call docker.onReceived(data)
            docker.process_received(data=data)
            return
        # save advance party from this source address
        party = self._cache_advance_party(data=data, source=source, destination=destination, connection=connection)
        assert party is not None and len(party) > 0, 'advance party error'
        # docker not exists, check the data to decide which docker should be created
        docker = self._create_docker(remote=source, local=destination, advance_party=party)
        if docker is not None:
            # cache docker for (remote, local)
            self._set_docker(docker=docker)
            # process advance parties one by one
            for item in party:
                docker.process_received(data=item)
            # remove advance party
            self._clear_advance_party(source=source, destination=destination, connection=connection)

    @abstractmethod
    def _cache_advance_party(self, data: bytes, source: Address, destination: Optional[Address],
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

    @abstractmethod
    def _clear_advance_party(self, source: Address, destination: Optional[Address], connection: Connection):
        """
        Clear all advance parties after docker created

        :param source:      remote address
        :param destination: local address
        :param connection:  current connection
        """
        raise NotImplemented

    # Override
    def connection_sent(self, data: bytes, source: Optional[Address], destination: Address, connection: Connection):
        # ignore this event
        pass
