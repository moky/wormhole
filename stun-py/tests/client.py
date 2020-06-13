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


SERVER_TEST = '127.0.0.1'

STUN_SERVERS = [
    # (SERVER_TEST, 3478),
    # (SERVER_GZ1, 3478),
    # (SERVER_GZ2, 3478),
    (SERVER_HK2, 3478),
]

LOCAL_IP = stun.get_local_ip()
LOCAL_PORT = 9527


class Client(stun.Client):

    def __init__(self, hub: udp.Hub):
        super().__init__()
        self.__hub = hub

    def stop(self):
        self.__hub.stop()

    def send(self, data: bytes, destination: tuple, source: Union[tuple, int] = None) -> int:
        try:
            return self.__hub.send(data=data, destination=destination, source=source)
        except socket.error:
            return -1

    def receive(self) -> (bytes, (str, int)):
        try:
            data, source, destination = self.__hub.receive(timeout=2)
            return data, source
        except socket.error:
            return None, None


def create_udp_client(local_host: str='127.0.0.1', local_port: int=9527) -> Client:
    # create a hub for sockets
    hub = udp.Hub()
    hub.open(host=local_host, port=local_port)
    hub.start()

    # create client
    client = Client(hub=hub)
    client.source_address = (local_host, local_port)
    return client


def detect(client: Client, stun_host, stun_port):
    print('----------------------------------------------------------------')
    print('-- Detection starts from: %s ...' % stun_host)
    msg, res = client.get_nat_type(stun_host=stun_host, stun_port=stun_port)
    print('-- Detection Result:', msg)
    if res is not None:
        print('-- External Address:', res.mapped_address)
    print('----------------------------------------------------------------')


if __name__ == '__main__':

    g_client = create_udp_client(local_host=LOCAL_IP, local_port=LOCAL_PORT)
    print('----------------------------------------------------------------')
    print('-- Local Address: (%s:%d)' % (LOCAL_IP, LOCAL_PORT))
    # create client
    for address in STUN_SERVERS:
        detect(client=g_client, stun_host=address[0], stun_port=address[1])
    # exit
    print('-- Local Address: (%s:%d)' % (LOCAL_IP, LOCAL_PORT))
    print('----------------------------------------------------------------')
    g_client.stop()
