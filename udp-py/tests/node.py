# -*- coding: utf-8 -*-

from typing import Optional

import udp
from udp import mtp


class Peer(mtp.Peer, udp.HubListener):

    #
    #   HubListener
    #
    def data_received(self, data: bytes, source: tuple, destination: tuple) -> Optional[bytes]:
        task = mtp.Arrival(payload=data, source=source, destination=destination)
        self.pool.append_arrival(task=task)
        return None


class Node(mtp.PeerDelegate):

    def __init__(self, host: str, port: int):
        super().__init__()
        self.__local_address = (host, port)
        self.__peer: Peer = None
        self.__hub: udp.Hub = None

    @property
    def local_address(self) -> tuple:
        return self.__local_address

    @property
    def peer(self) -> Peer:
        if self.__peer is None:
            self.__peer = self._create_peer()
        return self.__peer

    def _create_peer(self) -> Peer:
        peer = Peer()
        peer.delegate = self
        # peer.start()
        return peer

    @property
    def hub(self) -> udp.Hub:
        if self.__hub is None:
            self.__hub = self._create_hub()
        return self.__hub

    def _create_hub(self) -> udp.Hub:
        assert isinstance(self.__local_address, tuple), 'local address error'
        host = self.__local_address[0]
        port = self.__local_address[1]
        assert port > 0, 'invalid port: %d' % port
        hub = udp.Hub()
        hub.open(host=host, port=port)
        hub.add_listener(self.peer)
        # hub.start()
        return hub

    def start(self):
        # start peer
        if not self.peer.running:
            self.peer.start()
        # start hub
        if not self.hub.running:
            self.hub.start()

    def stop(self):
        # stop hub
        if self.__hub is not None:
            if self.__peer is not None:
                self.__hub.remove_listener(self.__peer)
            self.__hub.stop()
        # stop peer
        if self.__peer is not None:
            self.__peer.stop()

    def send_message(self, msg: bytes, destination: tuple) -> mtp.Departure:
        return self.peer.send_message(pack=msg, destination=destination, source=self.local_address)

    def send_command(self, cmd: bytes, destination: tuple) -> mtp.Departure:
        return self.peer.send_command(pack=cmd, destination=destination, source=self.local_address)

    #
    #   PeerDelegate
    #
    def send_data(self, data: bytes, destination: tuple, source: tuple) -> int:
        return self.hub.send(data=data, destination=destination, source=source)

    def received_command(self, cmd: bytes, source: tuple, destination: tuple) -> bool:
        print('received cmd (%d bytes) from %s to %s: %s' % (len(cmd), source, destination, cmd))
        return True

    def received_message(self, msg: bytes, source: tuple, destination: tuple) -> bool:
        print('received msg (%d bytes) from %s to %s: %s' % (len(msg), source, destination, msg))
        return True
