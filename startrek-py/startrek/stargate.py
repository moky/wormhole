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
import threading
import time
import weakref
from abc import ABC, abstractmethod
from typing import Optional, List, Iterable, Union

from .types import SocketAddress, AddressPairMap
from .skywalker import Runner

from .net import Connection, ConnectionDelegate, ConnectionState
from .net.state import StateOrder
from .port import Departure, Gate
from .port import Docker, DockerStatus, DockerDelegate
from .port.docker import status_from_state

from .stardocker import StarDocker


class DockerPool(AddressPairMap[Docker]):

    # Override
    def set(self, item: Optional[Docker],
            remote: Optional[SocketAddress], local: Optional[SocketAddress]) -> Optional[Docker]:
        # 1. remove cached item
        cached = super().remove(item=item, remote=remote, local=local)
        if cached is not None and cached is not item:
            Runner.async_task(coro=cached.close())
        # 2. set new item
        old = super().set(item=item, remote=remote, local=local)
        assert old is None, 'should not happen: %s' % old
        return cached

    # Override
    def remove(self, item: Optional[Docker],
               remote: Optional[SocketAddress], local: Optional[SocketAddress]) -> Optional[Docker]:
        cached = super().remove(item=item, remote=remote, local=local)
        if cached is not None and cached is not item:
            Runner.async_task(coro=cached.close())
        if item is not None:
            Runner.async_task(coro=item.close())
        return cached


class StarGate(Gate, ConnectionDelegate, ABC):
    """
        Star Gate
        ~~~~~~~~~

        @abstract methods:
            - _create_docker(advance_party, remote_address, local_address)
            - _cache_advance_party(data, connection)
            - _clear_advance_party(connection)
    """

    def __init__(self, delegate: DockerDelegate):
        super().__init__()
        self.__delegate_ref = weakref.ref(delegate)
        self.__docker_pool = self._create_docker_pool()
        self.__lock = threading.Lock()

    # noinspection PyMethodMayBeStatic
    def _create_docker_pool(self):
        return DockerPool()

    @property
    def delegate(self) -> Optional[DockerDelegate]:
        return self.__delegate_ref()

    # Override
    async def send_data(self, payload: Union[bytes, bytearray],
                        remote: SocketAddress, local: Optional[SocketAddress]) -> bool:
        worker = self._get_docker(remote=remote, local=local)
        if worker is None:
            # assert False, 'docker not found: %s -> %s' % (local, remote)
            return False
        elif not worker.alive:
            # assert False, 'docket not alive: %s -> %s' % (local, remote)
            return False
        return await worker.send_data(payload=payload)

    # Override
    async def send_ship(self, ship: Departure, remote: SocketAddress, local: Optional[SocketAddress]) -> bool:
        worker = self._get_docker(remote=remote, local=local)
        if worker is None:
            # assert False, 'docker not found: %s -> %s' % (local, remote)
            return False
        elif not worker.alive:
            # assert False, 'docket not alive: %s -> %s' % (local, remote)
            return False
        return await worker.send_ship(ship=ship)

    #
    #   Docker
    #

    @abstractmethod
    def _create_docker(self, parties: List[bytes],
                       remote: SocketAddress, local: Optional[SocketAddress]) -> Docker:
        """
        create new docker for received data

        :param parties: advance party
        :param remote:  remote address
        :param local:   local address
        :return docker
        """
        raise NotImplemented

    def _all_dockers(self) -> Iterable[Docker]:
        """ get a copy of all dockers """
        return self.__docker_pool.items

    def _remove_docker(self, docker: Optional[Docker],
                       remote: SocketAddress, local: Optional[SocketAddress]) -> Optional[Docker]:
        """ remove cached docker """
        return self.__docker_pool.remove(item=docker, remote=remote, local=local)

    def _get_docker(self, remote: SocketAddress, local: Optional[SocketAddress]) -> Optional[Docker]:
        """ get cached docker """
        return self.__docker_pool.get(remote=remote, local=local)

    def _set_docker(self, docker: Docker,
                    remote: SocketAddress, local: Optional[SocketAddress]) -> Optional[Docker]:
        """ cache docker """
        return self.__docker_pool.set(item=docker, remote=remote, local=local)

    #
    #   Processor
    #

    # Override
    async def process(self) -> bool:
        dockers = self._all_dockers()
        # 1. drive all dockers to process
        count = await self._drive_dockers(dockers=dockers)
        # 2. cleanup for dockers
        self._cleanup_dockers(dockers=dockers)
        return count > 0

    # noinspection PyMethodMayBeStatic
    async def _drive_dockers(self, dockers: Iterable[Docker]) -> int:
        count = 0
        for worker in dockers:
            if await worker.process():
                count += 1  # it's busy
        return count

    def _cleanup_dockers(self, dockers: Iterable[Docker]):
        now = time.time()
        for worker in dockers:
            if worker.closed:
                # remove docker which connection lost
                self._remove_docker(docker=worker, remote=worker.remote_address, local=worker.local_address)
            else:
                # clear expired tasks
                worker.purge(now=now)

    async def _heartbeat(self, connection: Connection):
        """ Send a heartbeat package('PING') to remote address """
        remote = connection.remote_address
        local = connection.local_address
        worker = self._get_docker(remote=remote, local=local)
        if worker is not None:
            await worker.heartbeat()

    #
    #   Connection Delegate
    #

    # Override
    async def connection_state_changed(self, previous: Optional[ConnectionState], current: Optional[ConnectionState],
                                       connection: Connection):
        # convert status
        s1 = status_from_state(state=previous)
        s2 = status_from_state(state=current)
        # 1. callback when status changed
        if s1 != s2:
            remote = connection.remote_address
            local = connection.local_address
            # try to get docker
            with self.__lock:
                old = self._get_docker(remote=remote, local=local)
                if old is None:
                    if s2 == DockerStatus.ERROR:
                        # connection closed and docker removed
                        return
                    # create & cache docker
                    worker = self._create_docker([], remote=remote, local=local)
                    self._set_docker(worker, remote=remote, local=local)
                else:
                    worker = old
            if old is None:
                assert isinstance(worker, StarDocker), 'docker error: %s, %s' % (remote, worker)
                # set connection for this docker
                await worker.set_connection(connection)
            # NOTICE: if the previous state is null, the docker maybe not
            #         created yet, this situation means the docker status
            #         not changed too, so no need to callback here.
            delegate = self.delegate
            if delegate is not None:
                await delegate.docker_status_changed(previous=s1, current=s2, docker=worker)
        # 2. heartbeat when connection expired
        index = -1 if current is None else current.index
        if index == StateOrder.EXPIRED:
            await self._heartbeat(connection=connection)

    # Override
    async def connection_received(self, data: bytes, connection: Connection):
        remote = connection.remote_address
        local = connection.local_address
        # try to get docker
        with self.__lock:
            old = self._get_docker(remote=remote, local=local)
            if old is None:
                # cache advance party for this connection
                party = self._cache_advance_party(data=data, connection=connection)
                assert party is not None and len(party) > 0, 'advance party error'
                # create & cache docker
                worker = self._create_docker(party, remote=remote, local=local)
                self._set_docker(worker, remote=remote, local=local)
            else:
                party = []
                worker = old
        if old is None:
            assert isinstance(worker, StarDocker), 'docker error: %s, %s' % (remote, worker)
            # set connection for this docker
            await worker.set_connection(connection)
            # process advance parties one by one
            for item in party:
                await worker.process_received(data=item)
            # remove advance party
            self._clear_advance_party(connection=connection)
        else:
            # docker exists, call docker.onReceived(data)
            await worker.process_received(data=data)

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
    async def connection_sent(self, sent: int, data: bytes, connection: Connection):
        # ignore event for sending success
        pass

    # Override
    async def connection_failed(self, error: Union[IOError, socket.error], data: bytes, connection: Connection):
        # ignore event for sending failed
        pass

    # Override
    async def connection_error(self, error: Union[IOError, socket.error], connection: Connection):
        # ignore event for receiving error
        pass
