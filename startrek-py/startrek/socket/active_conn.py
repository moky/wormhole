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
from typing import Optional

from ..types import SocketAddress
from ..skywalker import Runnable, Runner
from ..net import Hub

from .base_conn import BaseConnection


class ActiveConnection(BaseConnection, Runnable):
    """ Active connection for client """

    def __init__(self, remote: SocketAddress, local: Optional[SocketAddress]):
        super().__init__(remote=remote, local=local)
        self.__hub_ref = None

    @property  # protected
    def hub(self) -> Optional[Hub]:
        ref = self.__hub_ref
        if ref is not None:
            return ref()

    @property  # Override
    def closed(self) -> bool:
        return self.fsm is None

    # Override
    async def start(self, hub: Hub):
        self.__hub_ref = weakref.ref(hub)
        # 1. start state machine
        await self._start_machine()
        # 2. start an async task to check channel
        Runner.async_task(coro=self.run())
        # await self.run()

    # Override
    async def run(self):
        expired = 0
        last_time = 0
        interval = 8
        while True:
            await Runner.sleep(seconds=1.0)
            if self.closed:
                break
            now = time.time()
            try:
                sock = self.channel
                if sock is None or sock.closed:
                    # first time to try connecting (last_time == 0)?
                    # or connection lost, then try to reconnect again.
                    # check time interval for the trying here
                    if now < (last_time + interval):
                        continue
                    else:
                        # update last connect time
                        last_time = now
                    # get new socket channel via hub
                    hub = self.hub
                    assert hub is not None, 'hub not found: %s -> %s' % (self.local_address, self.remote_address)
                    # try to open a new socket channel from the hub.
                    # the returned socket channel is opened for connecting,
                    # but maybe failed,
                    # so set an expired time to close it after timeout;
                    # if failed to open a new socket channel,
                    # then extend the time interval for next trying.
                    sock = await self._open_channel(hub=hub)
                    if sock is not None:
                        # connect timeout after 2 minutes
                        expired = now + 128
                    elif interval < 128:
                        interval *= 2
                elif sock.alive:
                    # socket channel is normal, reset the time interval here.
                    # this will work when the current connection lost
                    interval = 8
                elif 0 < expired < now:
                    # connect timeout
                    await sock.close()
            except Exception as error:
                print('[Socket] active connection error: %s' % error)
