# -*- coding: utf-8 -*-

from typing import AnyStr

from udp import mtp

from .peer import Hub, Peer


class Node(mtp.PeerHandler):

    def __init__(self, peer: Peer=None, local_address: tuple=None, hub: Hub=None, pool: mtp.Pool=None):
        super().__init__()
        if peer is None:
            peer = self.__create_peer(local_address=local_address, hub=hub, pool=pool)
        self.__peer = peer
        peer.handler = self

    @staticmethod
    def __create_peer(local_address: tuple, hub: Hub=None, pool: mtp.Pool=None):
        peer = Peer(local_address=local_address, hub=hub, pool=pool)
        # peer.start()
        return peer

    @property
    def peer(self) -> Peer:
        return self.__peer

    def start(self):
        # start peer
        self.peer.start()

    def stop(self):
        # stop peer
        self.peer.stop()

    # noinspection PyMethodMayBeStatic
    def info(self, msg: AnyStr):
        print('> %s' % msg)

    #
    #   Send
    #
    def send_command(self, cmd: bytes, destination: tuple) -> mtp.Departure:
        pack = mtp.Package.new(data_type=mtp.Command, body=cmd)
        return self.peer.send_command(pack=pack, destination=destination)

    def send_message(self, msg: bytes, destination: tuple) -> mtp.Departure:
        pack = mtp.Package.new(data_type=mtp.Message, body=msg)
        return self.peer.send_message(pack=pack, destination=destination)

    #
    #   PeerHandler
    #
    def received_command(self, cmd: bytes, source: tuple, destination: tuple) -> bool:
        self.info('received cmd (%d bytes) from %s to %s: %s' % (len(cmd), source, destination, cmd))
        return True

    def received_message(self, msg: bytes, source: tuple, destination: tuple) -> bool:
        self.info('received msg (%d bytes) from %s to %s: %s' % (len(msg), source, destination, msg))
        return True
