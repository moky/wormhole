# -*- coding: utf-8 -*-
#
#   DMTP: Direct Message Transfer Protocol
#
#                                Written in 2020 by Moky <albert.moky@gmail.com>
#
# ==============================================================================
# MIT License
#
# Copyright (c) 2020 Albert Moky
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

from typing import Optional

from udp import Connection
from udp import HubListener, Hub as UDPHub
from udp.mtp import Package
from udp.mtp import Departure, Arrival, Pool
from udp.mtp import PeerDelegate, Peer as MTPPeer


class Hub(UDPHub, PeerDelegate):

    def send_data(self, data: bytes, destination: tuple, source: tuple) -> int:
        return self.send(data=data, destination=destination, source=source)


class Peer(MTPPeer, HubListener):

    def __init__(self, local_address: tuple, hub: Hub=None, pool: Pool=None):
        super().__init__(pool=pool)
        self.__local_address = local_address
        if hub is None:
            hub = Hub()
            hub.open(host=local_address[0], port=local_address[1])
            # hub.start()
            hub.add_listener(listener=self)
        self.__hub = hub
        self.delegate = hub

    @property
    def local_address(self) -> tuple:
        return self.__local_address

    @property
    def hub(self) -> Hub:
        return self.__hub

    def start(self):
        # start peer
        super().start()
        # start hub
        self.hub.start()

    def stop(self):
        # stop hub
        self.hub.stop()
        # stop peer
        super().stop()

    #
    #   Connections
    #

    def connect(self, remote_address: tuple) -> Optional[Connection]:
        return self.hub.connect(destination=remote_address, source=self.local_address)

    def disconnect(self, remote_address: tuple) -> set:
        return self.hub.disconnect(destination=remote_address, source=self.local_address)

    def get_connection(self, remote_address: tuple) -> Optional[Connection]:
        return self.hub.get_connection(destination=remote_address, source=self.local_address)

    def is_connected(self, remote_address: tuple) -> bool:
        conn = self.get_connection(remote_address=remote_address)
        if conn is not None:
            return conn.is_connected

    #
    #   Send
    #

    def send_command(self, pack: Package, destination: tuple, source: tuple=None) -> Departure:
        if source is None:
            source = self.local_address
        return super().send_command(pack=pack, destination=destination, source=source)

    def send_message(self, pack: Package, destination: tuple, source: tuple=None) -> Departure:
        if source is None:
            source = self.local_address
        return super().send_message(pack=pack, destination=destination, source=source)

    #
    #   HubListener
    #

    def data_received(self, data: bytes, source: tuple, destination: tuple) -> Optional[bytes]:
        task = Arrival(payload=data, source=source, destination=destination)
        self.pool.append_arrival(task=task)
        return None
