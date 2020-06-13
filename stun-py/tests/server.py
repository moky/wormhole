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


class Server(stun.Server):

    def __init__(self, hub: udp.Hub):
        super().__init__()
        self.__hub = hub

    def send(self, data: bytes, destination: tuple, source: Union[tuple, int] = None) -> int:
        try:
            return self.__hub.send(data=data, destination=destination, source=source)
        except socket.error:
            return -1

    def receive(self) -> (bytes, (str, int)):
        try:
            data, source, destination = self.__hub.receive()
            return data, source
        except socket.error:
            return None, None


def create_udp_server() -> Server:
    # create a hub for sockets
    hub = udp.Hub()
    hub.open(port=SERVER_PORT)
    hub.open(port=CHANGE_PORT)
    # hub.start()

    local_ip = stun.get_local_ip()
    if local_ip is None:
        source_address = ('0.0.0.0', SERVER_PORT)
    else:
        source_address = (local_ip, SERVER_PORT)

    # create server
    print('UDP server %s starting ...' % str(source_address))
    server = Server(hub=hub)
    server.source_address = source_address
    server.changed_address = CHANGED_ADDRESS
    server.change_port = CHANGE_PORT
    server.neighbour = NEIGHBOR_SERVER
    return server


def run_forever(server: Server):
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

    run_forever(create_udp_server())
