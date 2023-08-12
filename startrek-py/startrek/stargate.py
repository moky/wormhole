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
from abc import ABC, abstractmethod
from typing import Optional, List, Iterable, Union

from .types import Address, AddressPairMap
from .net import Connection, ConnectionDelegate, ConnectionState
from .port import Departure, Gate
from .port import Docker, DockerDelegate
from .port.docker import status_from_state


class DockerPool(AddressPairMap[Docker]):

    # Override
    def set(self, remote: Optional[Address], local: Optional[Address], item: Optional[Docker]):
        old = self.get(remote=remote, local=local)
        if old is not None and old is not item:
            self.remove(remote=remote, local=local, item=old)
        super().set(remote=remote, local=local, item=item)

    # Override
    def remove(self, remote: Optional[Address], local: Optional[Address], item: Optional[Docker]) -> Optional[Docker]:
        cached = super().remove(remote=remote, local=local, item=item)
        if cached is not None:
            if not cached.closed:
                cached.close()
            return cached


class StarGate(Gate, ConnectionDelegate, ABC):
    """
        Star Gate
        ~~~~~~~~~

        @abstract methods:
            - _create_docker(connection, advance_party)
            - _cache_advance_party(data, connection)
            - _clear_advance_party(connection)
    """

    def __init__(self, delegate: DockerDelegate):
        super().__init__()
        self.__delegate = weakref.ref(delegate)
        self.__docker_pool = self._create_docker_pool()

    # noinspection PyMethodMayBeStatic
    def _create_docker_pool(self):
        return DockerPool()

    @property
    def delegate(self) -> Optional[DockerDelegate]:
        return self.__delegate()

    # Override
    def send_data(self, payload: Union[bytes, bytearray], remote: Address, local: Optional[Address]) -> bool:
        docker = self._get_docker(remote=remote, local=local)
        if not (docker is None or docker.closed):
            return docker.send_data(payload=payload)

    # Override
    def send_ship(self, ship: Departure, remote: Address, local: Optional[Address]) -> bool:
        docker = self._get_docker(remote=remote, local=local)
        if not (docker is None or docker.closed):
            return docker.send_ship(ship=ship)

    #
    #   Docker
    #

    @abstractmethod
    def _create_docker(self, connection: Connection, advance_party: List[bytes]) -> Optional[Docker]:
        """
        create new docker for received data

        :param connection:    current connection
        :param advance_party: received data
        :return docker
        """
        raise NotImplemented

    def _all_dockers(self) -> Iterable[Docker]:
        """ get a copy of all dockers """
        return self.__docker_pool.items

    def _get_docker(self, remote: Address, local: Optional[Address]) -> Optional[Docker]:
        """ get cached docker """
        return self.__docker_pool.get(remote=remote, local=local)

    def _set_docker(self, remote: Address, local: Optional[Address], docker: Docker):
        """ cache docker """
        self.__docker_pool.set(remote=remote, local=local, item=docker)

    def _remove_docker(self, remote: Address, local: Optional[Address], docker: Optional[Docker]):
        """ remove cached docker """
        self.__docker_pool.remove(remote=remote, local=local, item=docker)

    #
    #   Processor
    #

    # Override
    def process(self) -> bool:
        dockers = self._all_dockers()
        # 1. drive all dockers to process
        count = self._drive_dockers(dockers=dockers)
        # 2. cleanup for dockers
        self._cleanup_dockers(dockers=dockers)
        return count > 0

    # noinspection PyMethodMayBeStatic
    def _drive_dockers(self, dockers: Iterable[Docker]) -> int:
        count = 0
        for worker in dockers:
            if worker.process():
                count += 1  # it's busy
        return count

    def _cleanup_dockers(self, dockers: Iterable[Docker]):
        for worker in dockers:
            if worker.closed:
                # remove docker which connection lost
                self._remove_docker(remote=worker.remote_address, local=worker.local_address, docker=worker)

    def _heartbeat(self, connection: Connection):
        """ Send a heartbeat package('PING') to remote address """
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
        if delegate is not None:
            s1 = status_from_state(state=previous)
            s2 = status_from_state(state=current)
            if s1 != s2:
                # callback
                remote = connection.remote_address
                local = connection.local_address
                docker = self._get_docker(remote=remote, local=local)
                # NOTICE: if the previous state is null, the docker maybe not
                #         created yet, this situation means the docker status
                #         not changed too, so no need to callback here.
                if docker is not None:
                    delegate.docker_status_changed(previous=s1, current=s2, docker=docker)
        # 2. heartbeat when connection expired
        if current == ConnectionState.EXPIRED:
            self._heartbeat(connection=connection)

    # Override
    def connection_received(self, data: bytes, connection: Connection):
        remote = connection.remote_address
        local = connection.local_address
        # get docker by (remote, local)
        docker = self._get_docker(remote=remote, local=local)
        if docker is not None:
            # docker exists, call docker.onReceived(data)
            docker.process_received(data=data)
            return
        # cache advance party for this connection
        party = self._cache_advance_party(data=data, connection=connection)
        assert party is not None and len(party) > 0, 'advance party error'
        # docker not exists, check the data to decide which docker should be created
        docker = self._create_docker(connection=connection, advance_party=party)
        if docker is not None:
            # cache docker for (remote, local)
            self._set_docker(remote=docker.remote_address, local=docker.local_address, docker=docker)
            # process advance parties one by one
            for item in party:
                docker.process_received(data=item)
            # remove advance party
            self._clear_advance_party(connection=connection)

    @abstractmethod
    def _cache_advance_party(self, data: bytes, connection: Connection) -> List[bytes]:
        """
        Cache the advance party before decide which docker to use

        :param data:        received data
        :param connection:  current connection
        :return all cached data
        """
        raise NotImplemented

    @abstractmethod
    def _clear_advance_party(self, connection: Connection):
        """
        Clear all advance parties after docker created

        :param connection:  current connection
        """
        raise NotImplemented

    # Override
    def connection_sent(self, sent: int, data: bytes, connection: Connection):
        # ignore event for sending success
        pass

    # Override
    def connection_failed(self, error: Union[IOError, socket.error], data: bytes, connection: Connection):
        # ignore event for sending failed
        pass

    # Override
    def connection_error(self, error: Union[IOError, socket.error], connection: Connection):
        # ignore event for receiving error
        pass
