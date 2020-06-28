# -*- coding: utf-8 -*-

from typing import Optional

import udp
from udp import mtp


class Hub(udp.Hub, mtp.PeerDelegate):

    def send_data(self, data: bytes, destination: tuple, source: tuple) -> int:
        return self.send(data=data, destination=destination, source=source)


class Peer(mtp.Peer, udp.HubListener):

    def __init__(self, local_address: tuple, hub: Hub=None, pool: mtp.Pool=None):
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

    def connect(self, remote_address: tuple) -> Optional[udp.Connection]:
        return self.hub.connect(destination=remote_address, source=self.local_address)

    def disconnect(self, remote_address: tuple) -> set:
        return self.hub.disconnect(destination=remote_address, source=self.local_address)

    def get_connection(self, remote_address: tuple) -> Optional[udp.Connection]:
        return self.hub.get_connection(destination=remote_address, source=self.local_address)

    def is_connected(self, remote_address: tuple) -> bool:
        conn = self.get_connection(remote_address=remote_address)
        if conn is not None:
            return conn.status == udp.ConnectionStatus.Connected

    #
    #   Send
    #

    def send_command(self, pack: mtp.Package, destination: tuple, source: tuple=None) -> mtp.Departure:
        if source is None:
            source = self.local_address
        return super().send_command(pack=pack, destination=destination, source=source)

    def send_message(self, pack: mtp.Package, destination: tuple, source: tuple=None) -> mtp.Departure:
        if source is None:
            source = self.local_address
        return super().send_message(pack=pack, destination=destination, source=source)

    #
    #   HubListener
    #
    def data_received(self, data: bytes, source: tuple, destination: tuple) -> Optional[bytes]:
        task = mtp.Arrival(payload=data, source=source, destination=destination)
        self.pool.append_arrival(task=task)
        return None
