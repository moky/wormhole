#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
from typing import Union

import udp
import stun


SERVER_LOC = '127.0.0.1'
SERVER_GZ1 = '134.175.87.98'
SERVER_GZ2 = '203.195.224.155'
SERVER_GZ3 = '129.204.94.164'

STUN_SERVERS = [
    # SERVER_LOC,
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

    def send(self, data: bytes, destination: tuple, source: Union[tuple, int] = None) -> int:
        try:
            return g_hub.send(data=data, destination=destination, source=source)
        except socket.error:
            return -1

    def receive(self) -> (bytes, (str, int)):
        try:
            data, source, destination = g_hub.receive(timeout=2)
            return data, source
        except socket.error:
            return None, None


# create a hub for sockets
g_hub = udp.Hub()
g_hub.open(host=LOCAL_IP, port=LOCAL_PORT)
g_hub.start()


def main():
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
    # exit
    g_hub.stop()


if __name__ == '__main__':
    main()
