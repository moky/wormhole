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
from ..net import Hub, Channel

from .base_conn import BaseConnection


class ActiveConnection(BaseConnection):
    """ Active connection for client """

    def __init__(self, remote: SocketAddress, local: Optional[SocketAddress], channel: Optional[Channel], hub: Hub):
        super().__init__(remote=remote, local=local, channel=channel)
        self.__hub_ref = weakref.ref(hub)
        self.__daemon = Daemon(target=self.run)

    @property
    def hub(self) -> Hub:
        return self.__hub_ref()

    # Override
    def start(self):
        super().start()
        self.__daemon.stop()
        self.__daemon.start()

    # Override
    def stop(self):
        self.__daemon.stop()
        super().stop()

    @property  # Override
    def closed(self) -> bool:
        return self._get_state_machine() is None

    def run(self):
        last_time = time.time()
        interval = 16
        while not self.closed:
            time.sleep(1.0)
            # check time interval
            now = time.time()
            if now < (last_time + interval):
                continue
            last_time = now
            if interval < 256:
                interval *= 2
            # check socket channel
            sock = self._get_channel()
            if sock is None or sock.closed:
                # get new socket channel via hub
                sock = self.hub.open(remote=self._remote, local=self._local)
                if sock is not None:
                    self._set_channel(channel=sock)
            elif sock.alive:
                # socket channel is normal
                interval = 16
            else:
                sock.close()
