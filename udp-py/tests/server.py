#! /usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Union

import sys
import os

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

import udp


SERVER_HOST = '0.0.0.0'
SERVER_PORT = 9394


class Server(udp.PeerDelegate):

    def __init__(self, hub: udp.Hub):
        super().__init__()
        self.__peer: udp.Peer = None
        hub.add_listener(self.peer)
        self.__hub = hub

    @property
    def peer(self) -> udp.Peer:
        if self.__peer is None:
            peer = udp.Peer()
            peer.delegate = self
            peer.start()
            self.__peer = peer
        return self.__peer

    #
    #   PeerDelegate
    #
    def send_data(self, data: bytes, destination: tuple, source: Union[tuple, int] = None) -> int:
        return self.__hub.send(data=data, destination=destination, source=source)

    def received_command(self, cmd: bytes, source: tuple, destination: tuple) -> bool:
        print('received cmd from %s to %s: %s' % (source, destination, cmd))
        return True

    def received_message(self, msg: bytes, source: tuple, destination: tuple) -> bool:
        print('received msg from %s to %s: %s' % (source, destination, msg))
        return True


def create_udp_server(port: int, host='0.0.0.0') -> Server:
    # create a hub for sockets
    hub = udp.Hub()
    hub.open(host=host, port=port)
    hub.start()

    # create server
    print('UDP server (%s:%d) starting ...' % (host, port))
    return Server(hub=hub)


if __name__ == '__main__':

    g_server = create_udp_server(host=SERVER_HOST, port=SERVER_PORT)
