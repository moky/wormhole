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

import time
import weakref
from abc import ABC, abstractmethod
from typing import Optional, List

from .types import SocketAddress, AddressPairObject
from .net import Connection
from .port import Arrival, Departure, ShipStatus
from .port import Docker, DockerStatus, DockerDelegate
from .port.docker import status_from_state

from .dock import Dock, LockedDock


class StarDocker(AddressPairObject, Docker, ABC):
    """
        Star Docker
        ~~~~~~~~~~~

        @abstract methods:
            - send_data(payload)
            - heartbeat()
            - _get_arrivals(data)
            - _check_arrival(ship)
    """

    def __init__(self, remote: SocketAddress, local: Optional[SocketAddress]):
        super().__init__(remote=remote, local=local)
        self.__dock = self._create_dock()
        self.__delegate_ref = None
        self.__conn_ref = None
        # remaining data to be sent
        self.__last_outgo: Optional[Departure] = None
        self.__last_fragments: List[bytes] = []

    # noinspection PyMethodMayBeStatic
    def _create_dock(self) -> Dock:
        """ Override for user-customized dock """
        return LockedDock()

    #
    #   Docker Event Handler
    #

    @property
    def delegate(self) -> Optional[DockerDelegate]:
        ref = self.__delegate_ref
        if ref is not None:
            return ref()

    @delegate.setter
    def delegate(self, keeper: DockerDelegate):
        self.__delegate_ref = None if keeper is None else weakref.ref(keeper)

    #
    #   Connection
    #

    @property
    def connection(self) -> Optional[Connection]:
        ref = self.__conn_ref
        if ref is not None:
            return ref()

    async def set_connection(self, conn: Optional[Connection]):
        """ set connection for this docker """
        # 1. replace with new connection
        old = self.connection
        if conn is not None:
            self.__conn_ref = weakref.ref(conn)
        # else:
        #     self.__conn_ref = None
        # 2. close old connection
        if old is not None and old is not conn:
            await old.close()

    #
    #   Flags
    #

    @property  # Override
    def closed(self) -> bool:
        if self.__conn_ref is None:
            # initializing
            return False
        conn = self.connection
        return conn is None or conn.closed

    @property  # Override
    def alive(self) -> bool:
        conn = self.connection
        return conn is not None and conn.alive

    @property  # Override
    def status(self) -> DockerStatus:
        conn = self.connection
        state = None if conn is None else conn.state
        return status_from_state(state=state)

    def __str__(self) -> str:
        mod = self.__module__
        cname = self.__class__.__name__
        return '<%s remote="%s" local="%s" status="%s">\n%s\n</%s module="%s">'\
               % (cname, self._remote, self._local, self.status, self.connection, cname, mod)

    def __repr__(self) -> str:
        mod = self.__module__
        cname = self.__class__.__name__
        return '<%s remote="%s" local="%s" status="%s">\n%s\n</%s module="%s">'\
               % (cname, self._remote, self._local, self.status, self.connection, cname, mod)

    # Override
    async def send_ship(self, ship: Departure) -> bool:
        return self.__dock.add_departure(ship=ship)

    # Override
    async def process_received(self, data: bytes):
        # 1. get income ship from received data
        ships = self._get_arrivals(data=data)
        if ships is None or len(ships) == 0:
            # waiting for more data
            return None
        delegate = self.delegate
        for income in ships:
            # 2. check income ship for response
            income = await self._check_arrival(ship=income)
            if income is None:
                # waiting for more fragment
                continue
            # 3. callback for processing income ship with completed data package
            if delegate is not None:
                await delegate.docker_received(ship=income, docker=self)

    @abstractmethod
    def _get_arrivals(self, data: bytes) -> List[Arrival]:
        """
        Get income ships from received data

        :param data: received data
        :return income ships carrying data package/fragments
        """
        raise NotImplemented

    @abstractmethod
    async def _check_arrival(self, ship: Arrival) -> Optional[Arrival]:
        """
        Check income ship for responding

        :param ship: income ship carrying data package/fragment/response
        :return income ship carrying completed data package
        """
        raise NotImplemented

    async def _check_response(self, ship: Arrival) -> Optional[Departure]:
        """
        Check and remove linked departure ship with same SN (and page index for fragment)

        :param ship: income ship with SN
        """
        # check response for linked departure ship (same SN)
        linked = self.__dock.check_response(ship=ship)
        if linked is None:
            # linked departure task not found, or not finished yet
            return None
        # all fragments responded, task finished
        delegate = self.delegate
        if delegate is not None:
            await delegate.docker_sent(ship=linked, docker=self)
        return linked

    def _assemble_arrival(self, ship: Arrival) -> Optional[Arrival]:
        """ Check received ship for completed package """
        return self.__dock.assemble_arrival(ship=ship)

    def _next_departure(self, now: float) -> Optional[Departure]:
        """ Get outgo ship from waiting queue """
        return self.__dock.next_departure(now=now)

    # Override
    def purge(self, now: float = 0) -> int:
        return self.__dock.purge(now=now)

    # Override
    async def close(self):
        await self.set_connection(conn=None)

    #
    #  Processor
    #

    # Override
    async def process(self) -> bool:
        # 1. get connection which is ready for sending data
        conn = self.connection
        if conn is None:
            # waiting for connection
            return False
        elif not conn.vacant:
            # connection is not ready for sending data
            return False
        # 2. get data waiting to be sent out
        outgo = self.__last_outgo
        fragments = self.__last_fragments
        if outgo is not None and len(fragments) > 0:
            # got remaining fragments from last outgo task
            self.__last_outgo = None
            self.__last_fragments = []
        else:
            # get next outgo task
            now = time.time()
            outgo = self._next_departure(now=now)
            if outgo is None:
                # nothing to do now, return false to let the thread have a rest
                return False
            elif outgo.get_status(now=now) == ShipStatus.FAILED:
                delegate = self.delegate
                if delegate is not None:
                    # callback for mission failed
                    error = TimeoutError('Request timeout')
                    await delegate.docker_failed(error=error, ship=outgo, docker=self)
                # task timeout, return True to process next one
                return True
            else:
                # get fragments from outgo task
                fragments = outgo.fragments
                if len(fragments) == 0:
                    # all fragments of this task have been sent already
                    # return True to process next one
                    return True
        # 3. process fragments of outgo task
        index = 0
        sent = 0
        try:
            for fra in fragments:
                sent = await conn.send(data=fra)
                if sent < len(fra):
                    # buffer overflow?
                    break
                else:
                    # assert sent == len(fra), 'length of fragment error: %d, %d' % (sent, len(fra))
                    index += 1
                    sent = 0  # clear counter
            if index < len(fragments):
                # task failed
                error = ConnectionError('only %d/%d fragments sent.' % (index, len(fragments)))
            else:
                # task done
                if outgo.is_important:
                    # this task needs response,
                    # so we cannot call 'docker_sent()' immediately
                    # until the remote responded.
                    pass
                else:
                    delegate = self.delegate
                    if delegate is not None:
                        await delegate.docker_sent(ship=outgo, docker=self)
                return True
        except Exception as e:
            # socket error, callback
            error = e
        # 4. remove sent fragments
        while index > 0:
            fragments.pop(0)
            index -= 1
        # remove partially sent data of next fragment
        if sent > 0:
            last = fragments.pop(0)
            fragments.insert(0, last[sent:])
        # 5. store remaining data
        self.__last_outgo = outgo
        self.__last_fragments = fragments
        # 6. callback for error
        delegate = self.delegate
        if delegate is not None:
            # await delegate.docker_failed(error=error, ship=outgo, docker=self)
            await delegate.docker_error(error=error, ship=outgo, docker=self)
        # task error
        return False
