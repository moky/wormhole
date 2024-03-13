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
from ..fsm import Daemon
from ..net import Hub

from .base_conn import BaseConnection


class ActiveConnection(BaseConnection):
    """ Active connection for client """

    def __init__(self, remote: SocketAddress, local: Optional[SocketAddress]):
        super().__init__(remote=remote, local=local)
        self.__hub_ref = None
        self.__daemon = Daemon(target=self.run)

    @property
    def hub(self) -> Hub:
        return self.__hub_ref()

    @property  # Override
    def closed(self) -> bool:
        return self.fsm is None

    # Override
    def start(self, hub: Hub):
        self.__hub_ref = weakref.ref(hub)
        # 1. start state machine
        self._start_machine()
        # 2. start a background thread to check channel
        self.__daemon.start()

    # protected
    def run(self):
        expired = 0
        last_time = 0
        interval = 16
        while not self.closed:
            time.sleep(1.0)
            #
            #  1. check time interval
            #
            now = time.time()
            if now < (last_time + interval):
                continue
            last_time = now
            if interval < 256:
                interval *= 2
            #
            #  2. check socket channel
            #
            try:
                sock = self.channel
                if sock is None or sock.closed:
                    # get new socket channel via hub
                    hub = self.hub
                    assert hub is not None, 'hub not found: %s -> %s' % (self.local_address, self.remote_address)
                    sock = self._open_channel(hub=hub)
                    if sock is None or sock.closed:
                        print('[Socket] cannot open channel: %s -> %s' % (self.local_address, self.remote_address))
                    else:
                        # connect timeout after 2 minutes
                        expired = now + 128
                elif sock.alive:
                    # socket channel is normal
                    interval = 16
                elif 0 < expired < now:
                    # connect timeout
                    sock.close()
            except Exception as error:
                print('[Socket] active connection error: %s' % error)
