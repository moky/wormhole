#! /usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional, Union

import sys
import os

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

import udp
import dmtp


SERVER_HOST = '0.0.0.0'
SERVER_PORT = 9394


class Server(dmtp.Server):

    def __init__(self, peer: udp.Peer, hub: udp.Hub):
        super().__init__()
        peer.delegate = self
        self.__peer = peer
        self.__hub = hub
        self.__locations = {}

    def set_location(self, value: dmtp.LocationValue) -> bool:
        if value.ip is None or value.port == 0:
            return False
        # TODO: verify mapped address with signature
        self.__locations[value.id] = value
        self.__locations[(value.ip, value.port)] = value
        print('location updated: %s' % value)
        return True

    def get_location(self, uid: str = None, source: tuple = None) -> Optional[dmtp.LocationValue]:
        if uid is None:
            return self.__locations.get(source)
        else:
            return self.__locations.get(uid)

    def process_message(self, msg: dmtp.Message, source: tuple) -> bool:
        print('received msg: %s' % msg)
        return True

    def send_command(self, cmd: dmtp.Command, destination: tuple):
        self.__peer.send_command(data=cmd.data, destination=destination)

    def send_message(self, msg: dmtp.Message, destination: tuple):
        self.__peer.send_message(data=msg.data, destination=destination)

    #
    #   PeerDelegate
    #
    def send_data(self, data: bytes, destination: tuple, source: Union[tuple, int] = None) -> int:
        self.__hub.send(data=data, destination=destination, source=source)
        return 0


def create_udp_server(port: int, host='0.0.0.0') -> Server:
    # create a peer
    peer = udp.Peer()

    # create a hub for sockets
    hub = udp.Hub()
    hub.open(host=host, port=port)
    hub.add_listener(peer)

    # create server
    server = Server(peer=peer, hub=hub)

    # starting
    print('UDP server (%s:%d) starting ...' % (host, port))
    peer.start()
    hub.start()
    return server


if __name__ == '__main__':
    g_server = create_udp_server(host=SERVER_HOST, port=SERVER_PORT)
