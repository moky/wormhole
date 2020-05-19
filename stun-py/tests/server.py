#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import socket

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
        # socket 1 for normal request
        sock1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock1.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock1.settimeout(2)
        sock1.bind(('0.0.0.0', LOCAL_PORT))
        self.__socket1 = sock1
        # socket 2 for "change port"
        sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock2.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock2.settimeout(2)
        sock2.bind(('0.0.0.0', ANOTHER_PORT))
        self.__socket2 = sock2
        # socket 3 for "change IP & port"
        sock3 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock3.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock3.settimeout(2)
        sock3.bind(('0.0.0.0', REDIRECTED_PORT))
        self.__socket3 = sock3

    def send(self, data: bytes, remote_host: str, remote_port: int, local_port: int=0) -> int:
        try:
            if local_port == LOCAL_PORT:
                return self.__socket1.sendto(data, (remote_host, remote_port))
            elif local_port == ANOTHER_PORT:
                return self.__socket2.sendto(data, (remote_host, remote_port))
            elif local_port == REDIRECTED_PORT:
                return self.__socket3.sendto(data, (remote_host, remote_port))
            else:
                assert local_port is 0, 'local port error: %d' % local_port
                return self.__socket1.sendto(data, (remote_host, remote_port))
        except socket.error:
            return -1

    def receive(self, buffer_size: int=2048) -> (bytes, (str, int)):
        try:
            return self.__socket1.recvfrom(buffer_size)
        except socket.error:
            return None, None


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
