#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import random
import time
from typing import Union

import sys
import os

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

import udp


SERVER_HOST = '127.0.0.1'
SERVER_PORT = 9394

CLIENT_HOST = '0.0.0.0'
CLIENT_PORT = random.choice(range(9900, 9999))


class Client(udp.PeerDelegate):

    def __init__(self, hub: udp.Hub):
        super().__init__()
        self.__peer: udp.Peer = None
        hub.add_listener(self.peer)
        self.__hub = hub
        self.server_address = None

    @property
    def peer(self) -> udp.Peer:
        if self.__peer is None:
            peer = udp.Peer()
            peer.delegate = self
            peer.start()
            self.__peer = peer
        return self.__peer

    def stop(self):
        self.__peer.stop()
        self.__hub.remove_listener(self.__peer)
        self.__hub.stop()

    def send_message(self, msg: bytes, destination: tuple) -> udp.Departure:
        return self.peer.send_message(pack=msg, destination=destination)

    #
    #   PeerDelegate
    #
    def send_data(self, data: bytes, destination: tuple, source: Union[tuple, int]=None) -> int:
        return self.__hub.send(data=data, destination=destination, source=source)

    def received_command(self, cmd: bytes, source: tuple, destination: tuple) -> bool:
        print('received cmd (%d bytes) from %s to %s: %s' % (len(cmd), source, destination, cmd))
        return True

    def received_message(self, msg: bytes, source: tuple, destination: tuple) -> bool:
        print('received msg (%d bytes) from %s to %s: %s' % (len(msg), source, destination, msg))
        return True


def create_udp_client(local_address: tuple, server_address: tuple):

    # create a hub for sockets
    hub = udp.Hub()
    hub.open(host=local_address[0], port=local_address[1])
    hub.start()

    # create client
    print('UDP client %s -> %s starting ...' % (local_address, server_address))
    client = Client(hub=hub)
    client.server_address = server_address
    return client


def send_msg(msg: str, client: Client):
    data = msg.encode('utf-8')
    address = g_client.server_address
    print('sending msg (%d bytes): "%s" to %s' % (len(data), msg, address))
    client.send_message(msg=data, destination=address)


if __name__ == '__main__':

    g_client = create_udp_client(local_address=(CLIENT_HOST, CLIENT_PORT),
                                 server_address=(SERVER_HOST, SERVER_PORT))
    text = ''
    for i in range(1024):
        text += ' Hello!'
    # test send
    counter = 0
    while True:
        counter += 2
        if counter > 32:
            break
        s = '%d sheep:%s' % (counter, text)
        send_msg(msg=s, client=g_client)
        time.sleep(2)
    # exit
    g_client.stop()
