#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
from typing import Union

import udp
import stun

import sys
import os

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

from tests.srv_cnf import *


class UDPServer(stun.Server):

    def __init__(self):
        super().__init__()

    def send(self, data: bytes, destination: tuple, source: Union[tuple, int] = None) -> int:
        try:
            return g_hub.send(data=data, destination=destination, source=source)
        except socket.error:
            return -1

    def receive(self) -> (bytes, (str, int)):
        try:
            data, source, destination = g_hub.receive()
            return data, source
        except socket.error:
            return None, None


# create a hub for sockets
g_hub = udp.Hub()
g_hub.open(port=LOCAL_PORT)
g_hub.open(port=ANOTHER_PORT)
g_hub.open(port=REDIRECTED_PORT)


def main():
    # create server
    server = UDPServer()
    server.source_address = (LOCAL_IP, LOCAL_PORT)
    if len(NEIGHBOR_SERVERS) == 1:
        server.changed_address = NEIGHBOR_SERVERS[0]
        server.neighbour_address = NEIGHBOR_SERVERS[0]
    elif len(NEIGHBOR_SERVERS) == 2:
        server.changed_address = NEIGHBOR_SERVERS[0]
        server.neighbour_address = NEIGHBOR_SERVERS[1]
    server.another_port = ANOTHER_PORT
    server.redirected_port = REDIRECTED_PORT
    # GO!
    server.info('STUN server started')
    while True:
        try:
            data, address = server.receive()
            if data is None:
                continue
            # noinspection PyTypeChecker
            server.handle(data=data, remote_ip=address[0], remote_port=address[1])
        except Exception as error:
            print('error: %s' % error)


if __name__ == '__main__':
    main()
