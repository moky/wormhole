#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import socket

import stun

SERVER_GZ1 = '134.175.87.98'
SERVER_GZ2 = '203.195.224.155'
SERVER_GZ3 = '129.204.94.164'

STUN_SERVERS = [
    SERVER_GZ1,
    # SERVER_GZ2,
    # SERVER_GZ3,
]
STUN_PORT = 3478

LOCAL_IP = '0.0.0.0'
LOCAL_PORT = 9394


class UDPClient(stun.Client):

    def __init__(self):
        super().__init__()
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(2)
        sock.bind(('0.0.0.0', LOCAL_PORT))
        self.__socket = sock

    def send(self, data: bytes, remote_host: str, remote_port: int) -> int:
        try:
            return self.__socket.sendto(data, (remote_host, remote_port))
        except socket.error:
            return -1

    def receive(self, buffer_size: int=2048) -> (bytes, tuple):
        try:
            return self.__socket.recvfrom(buffer_size)
        except socket.error:
            return None, None


if __name__ == '__main__':
    # create client
    client = UDPClient()
    client.source_address = (LOCAL_IP, LOCAL_PORT)
    for host in STUN_SERVERS:
        print('--------------------------------')
        print('-- Detection starts from: %s ...' % host)
        msg, res = client.get_nat_type(stun_host=host, stun_port=STUN_PORT)
        print('-- Detection Result:', msg)
        if res is not None:
            print('-- External Address:', res.mapped_address)
        print('--------------------------------')
