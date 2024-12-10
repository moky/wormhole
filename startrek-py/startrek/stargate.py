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
from typing import Optional, Iterable, Union

from .types import SocketAddress, AddressPairMap

from .net import Connection, ConnectionDelegate, ConnectionState
from .net.state import StateOrder
from .port import Departure, Gate
from .port import Porter, PorterStatus, PorterDelegate
from .port.docker import status_from_state

from .stardocker import StarPorter


class PorterPool(AddressPairMap[Porter]):

    # Override
    def set(self, item: Optional[Porter],
            remote: Optional[SocketAddress], local: Optional[SocketAddress]) -> Optional[Porter]:
        # remove cached item first
        cached = super().remove(item=item, remote=remote, local=local)
        # if cached is not None and cached is not item:
        #     Runner.async_task(coro=cached.close())
        old = super().set(item=item, remote=remote, local=local)
        assert old is None, 'should not happen: %s' % old
        return cached

    # # Override
    # def remove(self, item: Optional[Porter],
    #            remote: Optional[SocketAddress], local: Optional[SocketAddress]) -> Optional[Porter]:
    #     cached = super().remove(item=item, remote=remote, local=local)
    #     if cached is not None and cached is not item:
    #         Runner.async_task(coro=cached.close())
    #     if item is not None:
    #         Runner.async_task(coro=item.close())
    #     return cached


class StarGate(Gate, ConnectionDelegate, ABC):
    """
        Star Gate
        ~~~~~~~~~

        @abstract methods:
            - _create_porter(remote_address, local_address)
    """

    def __init__(self, delegate: PorterDelegate):
        super().__init__()
        self.__delegate_ref = weakref.ref(delegate)
        self.__porter_pool = self._create_porter_pool()
        self.__lock = threading.Lock()

    # noinspection PyMethodMayBeStatic
    def _create_porter_pool(self):
        return PorterPool()

    @property
    def delegate(self) -> Optional[PorterDelegate]:
        return self.__delegate_ref()

    # Override
    async def send_data(self, payload: Union[bytes, bytearray],
                        remote: SocketAddress, local: Optional[SocketAddress]) -> bool:
        docker = self._get_porter(remote=remote, local=local)
        if docker is None:
            # assert False, 'docker not found: %s -> %s' % (local, remote)
            return False
        elif not docker.alive:
            # assert False, 'docket not alive: %s -> %s' % (local, remote)
            return False
        return await docker.send_data(payload=payload)

    # Override
    async def send_ship(self, ship: Departure, remote: SocketAddress, local: Optional[SocketAddress]) -> bool:
        docker = self._get_porter(remote=remote, local=local)
        if docker is None:
            # assert False, 'docker not found: %s -> %s' % (local, remote)
            return False
        elif not docker.alive:
            # assert False, 'docket not alive: %s -> %s' % (local, remote)
            return False
        return await docker.send_ship(ship=ship)

    #
    #   Docker
    #

    @abstractmethod
    def _create_porter(self,  remote: SocketAddress, local: Optional[SocketAddress]) -> Porter:
        """
        create new docker for received data

        :param remote:  remote address
        :param local:   local address
        :return docker
        """
        raise NotImplemented

    def _all_porters(self) -> Iterable[Porter]:
        """ get a copy of all dockers """
        return self.__porter_pool.items

    def _remove_porter(self, porter: Optional[Porter],
                       remote: SocketAddress, local: Optional[SocketAddress]) -> Optional[Porter]:
        """ remove cached docker """
        return self.__porter_pool.remove(item=porter, remote=remote, local=local)

    def _get_porter(self, remote: SocketAddress, local: Optional[SocketAddress]) -> Optional[Porter]:
        """ get cached docker """
        return self.__porter_pool.get(remote=remote, local=local)

    def _set_porter(self, porter: Porter,
                    remote: SocketAddress, local: Optional[SocketAddress]) -> Optional[Porter]:
        """ cache docker """
        return self.__porter_pool.set(item=porter, remote=remote, local=local)

    async def _dock(self, connection: Connection, new_porter: bool) -> Optional[Porter]:
        """ get docker with connection """
        #
        #  0. pre-checking
        #
        remote = connection.remote_address
        local = connection.local_address
        docker = self._get_porter(remote=remote, local=local)
        if docker is not None:
            return docker
        #
        #  1. lock to check
        #
        with self.__lock:
            # check again
            docker = self._get_porter(remote=remote, local=local)
            if docker is not None:
                # found
                return docker
            elif not new_porter:
                # no need to create new porter
                return None
            # docker not exists, create new docker
            docker = self._create_porter(remote=remote, local=local)
            cached = self._set_porter(docker, remote=remote, local=local)
        #
        #  2. close old docker
        #
        if cached is None or cached is docker:
            pass
        else:
            await cached.close()
        #
        #  3. set connection for this docker
        #
        if isinstance(docker, StarPorter):
            await docker.set_connection(connection)
        else:
            assert False, 'docker error: %s, %s' % (remote, docker)
        return docker

    #
    #   Processor
    #

    # Override
    async def process(self) -> bool:
        dockers = self._all_porters()
        # 1. drive all dockers to process
        count = await self._drive_porters(porters=dockers)
        # 2. cleanup for dockers
        await self._cleanup_porters(porters=dockers)
        return count > 0

    # noinspection PyMethodMayBeStatic
    async def _drive_porters(self, porters: Iterable[Porter]) -> int:
        count = 0
        for docker in porters:
            if await docker.process():
                count += 1  # it's busy
        return count

    async def _cleanup_porters(self, porters: Iterable[Porter]):
        now = time.time()
        for docker in porters:
            if not docker.closed:
                # docker connected,
                # clear expired tasks
                docker.purge(now=now)
                continue
            # remove docker when connection closed
            cached = self._remove_porter(porter=docker, remote=docker.remote_address, local=docker.local_address)
            if cached is None or cached is docker:
                pass
            else:
                await cached.close()

    async def _heartbeat(self, connection: Connection):
        """ Send a heartbeat package('PING') to remote address """
        remote = connection.remote_address
        local = connection.local_address
        docker = self._get_porter(remote=remote, local=local)
        if docker is not None:
            await docker.heartbeat()

    #
    #   Connection Delegate
    #

    # Override
    async def connection_state_changed(self, previous: Optional[ConnectionState], current: Optional[ConnectionState],
                                       connection: Connection):
        # convert status
        s1 = status_from_state(state=previous)
        s2 = status_from_state(state=current)
        #
        #  1. callback when status changed
        #
        if s1 != s2:
            not_finished = s2 != PorterStatus.ERROR
            docker = await self._dock(connection=connection, new_porter=not_finished)
            if docker is None:
                # connection closed and docker removed
                return
            # callback for docker status
            delegate = self.delegate
            if delegate is not None:
                await delegate.porter_status_changed(previous=s1, current=s2, porter=docker)
        #
        #  2. heartbeat when connection expired
        #
        index = -1 if current is None else current.index
        if index == StateOrder.EXPIRED:
            await self._heartbeat(connection=connection)

    # Override
    async def connection_received(self, data: bytes, connection: Connection):
        docker = await self._dock(connection=connection, new_porter=True)
        if docker is None:
            assert False, 'failed to create docker: %s' % connection
        else:
            await docker.process_received(data=data)

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
