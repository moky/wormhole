# -*- coding: utf-8 -*-

from typing import AnyStr

from dmtp.mtp.tlv import Data
from dmtp.mtp import PeerHandler, Pool, Departure, Package, Command, Message

from .peer import Hub, Peer


class Node(PeerHandler):

    def __init__(self, peer: Peer=None, local_address: tuple=None, hub: Hub=None, pool: Pool=None):
        super().__init__()
        if peer is None:
            peer = self.__create_peer(local_address=local_address, hub=hub, pool=pool)
        self.__peer = peer
        peer.handler = self

    # noinspection PyMethodMayBeStatic
    def __create_peer(self, local_address: tuple, hub: Hub=None, pool: Pool=None):
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
    def send_command(self, cmd: Data, destination: tuple) -> Departure:
        pack = Package.new(data_type=Command, body=cmd)
        return self.peer.send_command(pack=pack, destination=destination)

    def send_message(self, msg: Data, destination: tuple) -> Departure:
        pack = Package.new(data_type=Message, body=msg)
        return self.peer.send_message(pack=pack, destination=destination)

    #
    #   PeerHandler
    #
    def received_command(self, cmd: Data, source: tuple, destination: tuple) -> bool:
        self.info('received cmd (%d bytes) from %s to %s: %s' % (cmd.length, source, destination, cmd.get_bytes()))
        return True

    def received_message(self, msg: Data, source: tuple, destination: tuple) -> bool:
        self.info('received msg (%d bytes) from %s to %s: %s' % (msg.length, source, destination, msg.get_bytes()))
        return True

    def received_error(self, data: Data, source: tuple, destination: tuple):
        self.info('received error (%d bytes) from %s to %s: %s' % (data.length, source, destination, data.get_bytes()))
