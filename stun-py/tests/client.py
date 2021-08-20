#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import sys
import os
import time
from typing import Optional, Union

from udp.ba import Data
from udp import Connection
from udp import Channel, DiscreteChannel
from udp import ConnectionDelegate
from udp import Hub, ActivePackageHub

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

import stun


# SERVER_TEST = '127.0.0.1'
SERVER_TEST = Hub.inet_address()

STUN_SERVERS = [
    (SERVER_TEST, 3478),
    # (SERVER_GZ1, 3478),
    # (SERVER_GZ2, 3478),
    # (SERVER_HK2, 3478),
]

LOCAL_IP = Hub.inet_address()
LOCAL_PORT = 9527


class ClientHub(ActivePackageHub):

    def create_channel(self, remote: tuple, local: Optional[tuple] = None) -> Channel:
        channel = DiscreteChannel(remote=remote, local=local)
        channel.configure_blocking(False)
        return channel


class Client(stun.Client, ConnectionDelegate):

    hub: ClientHub = None

    def __init__(self, host: str, port: int):
        super().__init__(host=host, port=port)
        self.__cargoes = []

    # noinspection PyMethodMayBeStatic
    def info(self, msg: str):
        print('> %s' % msg)

    def connection_state_changing(self, connection: Connection, current_state, next_state):
        self.info('!!! connection (%s, %s) state changed: %s -> %s'
                  % (connection.local_address, connection.remote_address, current_state, next_state))

    def connection_data_received(self, connection: Connection, remote: tuple, wrapper, payload: bytes):
        self.__cargoes.append((payload, remote))

    def receive(self) -> (Optional[bytes], Optional[tuple]):
        data = None
        remote = None
        expired = time.time() + 2.0
        while True:
            if len(self.__cargoes) > 0:
                cargo = self.__cargoes.pop(0)
                data = cargo[0]
                remote = cargo[1]
                break
            if time.time() > expired:
                break
            else:
                time.sleep(0.2)
                self.hub.tick()
        return data, remote

    def send(self, data: Data, destination: tuple, source: Union[tuple, int] = None) -> bool:
        try:
            if source is None:
                source = self.source_address
            elif isinstance(source, int):
                source = (self.source_address[0], source)
            self.hub.send_message(body=data.get_bytes(), source=source, destination=destination)
            return True
        except socket.error:
            return False

    def detect(self, stun_host: str, stun_port: int):
        print('----------------------------------------------------------------')
        print('-- Detection starts from: %s ...' % stun_host)
        res = self.get_nat_type(stun_host=stun_host, stun_port=stun_port)
        print('-- Detection Result:', res.get('NAT'))
        print('-- External Address:', res.get('MAPPED-ADDRESS'))
        print('----------------------------------------------------------------')


if __name__ == '__main__':

    # create client
    g_client = Client(host=LOCAL_IP, port=LOCAL_PORT)

    Client.hub = ClientHub(delegate=g_client)

    print('----------------------------------------------------------------')
    print('-- Local Address: (%s:%d)' % (LOCAL_IP, LOCAL_PORT))
    # create client
    for address in STUN_SERVERS:
        g_client.detect(stun_host=address[0], stun_port=address[1])
    # exit
    print('-- Local Address: (%s:%d)' % (LOCAL_IP, LOCAL_PORT))
    print('----------------------------------------------------------------')
