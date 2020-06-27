# -*- coding: utf-8 -*-

from typing import Optional, AnyStr

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
            self.delegate = hub
        self.__hub = hub

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


class Node(mtp.PeerHandler):

    def __init__(self, peer: Peer=None, local_address: tuple=None, hub: Hub=None, pool: mtp.Pool=None):
        super().__init__()
        if peer is None:
            peer = self.__create_peer(local_address=local_address, hub=hub, pool=pool)
        self.__peer: Peer = peer
        peer.handler = self

    @staticmethod
    def __create_peer(local_address: tuple, hub: Hub=None, pool: mtp.Pool=None):
        peer = Peer(local_address=local_address, hub=hub, pool=pool)
        # peer.start()
        return peer

    @property
    def peer(self) -> Peer:
        return self.__peer

    @property
    def local_address(self) -> tuple:
        return self.peer.local_address

    def start(self):
        # start peer
        self.peer.start()

    def stop(self):
        # stop peer
        self.peer.stop()

    # noinspection PyMethodMayBeStatic
    def info(self, msg: AnyStr):
        print('> %s' % msg)

    def send_command(self, cmd: bytes, destination: tuple) -> mtp.Departure:
        pack = mtp.Package.new(data_type=mtp.Command, body=cmd)
        return self.peer.send_command(pack=pack, destination=destination, source=self.local_address)

    def send_message(self, msg: bytes, destination: tuple) -> mtp.Departure:
        pack = mtp.Package.new(data_type=mtp.Message, body=msg)
        return self.peer.send_message(pack=pack, destination=destination, source=self.local_address)

    #
    #   PeerHandler
    #
    def received_command(self, cmd: bytes, source: tuple, destination: tuple) -> bool:
        self.info('received cmd (%d bytes) from %s to %s: %s' % (len(cmd), source, destination, cmd))
        return True

    def received_message(self, msg: bytes, source: tuple, destination: tuple) -> bool:
        self.info('received msg (%d bytes) from %s to %s: %s' % (len(msg), source, destination, msg))
        return True
