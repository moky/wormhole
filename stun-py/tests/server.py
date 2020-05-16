#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import socket

import stun


SERVER_ANY = '0.0.0.0'
SERVER_GZ1 = '134.175.87.98'
SERVER_GZ2 = '203.195.224.155'
SERVER_GZ3 = '129.204.94.164'

NEIGHBOR_SERVERS = [
    # (SERVER_GZ1, 3478),
    # (SERVER_GZ2, 3478),
    (SERVER_GZ3, 3478),
]

LOCAL_IP = SERVER_GZ1
# LOCAL_IP = SERVER_ANY

LOCAL_PORT = 3478
ANOTHER_PORT = 3480
REDIRECTED_PORT = 3479


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

    def send(self, data: bytes, remote_host: str, remote_port: int, local_port: int=0) -> int:
        try:
            if local_port == ANOTHER_PORT:
                return self.__socket2.sendto(data, (remote_host, remote_port))
            else:
                assert local_port is 0 or local_port == LOCAL_PORT, 'local port error: %d' % local_port
                return self.__socket1.sendto(data, (remote_host, remote_port))
        except socket.error:
            return -1

    def receive(self, buffer_size: int=2048) -> (bytes, tuple):
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
