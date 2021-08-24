#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import sys
import os
import time
import weakref
from typing import Optional, Union, Dict

from udp.ba import ByteArray
from udp import Channel, DiscreteChannel
from udp import Connection, ConnectionDelegate
from udp import Hub, BaseHub, BaseConnection

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

import stun


class ClientHub(BaseHub):

    def __init__(self, delegate: ConnectionDelegate):
        super().__init__()
        self.__delegate = weakref.ref(delegate)
        self.__connections: Dict[tuple, Connection] = {}
        self.__sockets: Dict[tuple, socket.socket] = {}

    @property
    def delegate(self) -> ConnectionDelegate:
        return self.__delegate()

    def bind(self, local: tuple) -> Connection:
        sock = self.__sockets.get(local)
        if sock is None:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            sock.bind(local)
            sock.setblocking(False)
            self.__sockets[local] = sock
        return self.connect(remote=None, local=local)

    # Override
    def create_connection(self, remote: Optional[tuple], local: Optional[tuple]) -> Connection:
        conn = self.__connections.get(local)
        if conn is None:
            conn = self.__create_connection(remote=None, local=local)
            self.__connections[local] = conn
        return conn

    def __create_connection(self, remote: Optional[tuple], local: Optional[tuple]) -> Connection:
        # create connection with channel
        sock = self.create_channel(remote=remote, local=local)
        conn = BaseConnection(remote=remote, local=local, channel=sock)
        # set delegate
        if conn.delegate is None:
            conn.delegate = self.delegate
        # start FSM
        conn.start()
        return conn

    def create_channel(self, remote: Optional[tuple], local: Optional[tuple]) -> Channel:
        sock = self.__sockets.get(local)
        if sock is not None:
            return DiscreteChannel(sock=sock)
        else:
            raise LookupError('failed to get channel: %s -> %s' % (remote, local))


class Client(stun.Client, ConnectionDelegate):

    def __init__(self, host: str, port: int):
        super().__init__(host=host, port=port)
        self.__cargoes = []
        self.__hub = ClientHub(delegate=self)
        self.__hub.bind(local=self.source_address)

    @property
    def hub(self) -> ClientHub:
        return self.__hub

    # noinspection PyMethodMayBeStatic
    def info(self, msg: str):
        print('> ', msg)

    # noinspection PyMethodMayBeStatic
    def error(self, msg: str):
        print('ERROR> ', msg)

    # Override
    def connection_state_changing(self, connection: Connection, current_state, next_state):
        self.info('!!! connection (%s, %s) state changed: %s -> %s'
                  % (connection.local_address, connection.remote_address, current_state, next_state))

    # Override
    def connection_data_received(self, connection: Connection, remote: tuple, wrapper, payload: bytes):
        self.__cargoes.append((payload, remote))

    # Override
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
                self.__hub.tick()
        return data, remote

    # Override
    def send(self, data: ByteArray, destination: tuple, source: Union[tuple, int] = None) -> bool:
        try:
            if source is None:
                source = self.source_address
            elif isinstance(source, int):
                source = (self.source_address[0], source)
            self.__hub.send(data=data.get_bytes(), source=source, destination=destination)
            return True
        except socket.error:
            return False

    def detect(self, stun_host: str, stun_port: int):
        print('----------------------------------------------------------------')
        print('-- Detection starts from:', stun_host)
        res = self.get_nat_type(stun_host=stun_host, stun_port=stun_port)
        print('-- Detection Result:', res.get('NAT'))
        print('-- External Address:', res.get('MAPPED-ADDRESS'))
        print('----------------------------------------------------------------')


# SERVER_TEST = '127.0.0.1'
SERVER_TEST = Hub.inet_address()

STUN_SERVERS = [
    # ("stun.xten.com", 3478),
    ("stun.voipbuster.com", 3478),
    # ("stun.sipgate.net", 3478),
    # ("stun.ekiga.net", 3478),
    # ("stun.schlund.de", 3478),
    # ("stun.voipstunt.com", 3478),  # Full Cone NAT?
    # ("stun.counterpath.com", 3478),
    # ("stun.1und1.de", 3478),
    # ("stun.gmx.net", 3478),
    # ("stun.callwithus.com", 3478),
    # ("stun.counterpath.net", 3478),
    # ("stun.internetcalls.com", 3478),

    (SERVER_TEST, 3478),
    # (SERVER_GZ1, 3478),
    # (SERVER_GZ2, 3478),
    # (SERVER_HK2, 3478),
]

LOCAL_IP = Hub.inet_address()
LOCAL_PORT = 9527


if __name__ == '__main__':

    # create client
    g_client = Client(host=LOCAL_IP, port=LOCAL_PORT)

    print('================================================================')
    print('== Local Address: (%s:%d)' % (LOCAL_IP, LOCAL_PORT))
    # create client
    for address in STUN_SERVERS:
        g_client.detect(stun_host=address[0], stun_port=address[1])
    # exit
    print('== Local Address: (%s:%d)' % (LOCAL_IP, LOCAL_PORT))
    print('================================================================')
