#! /usr/bin/env python3
# -*- coding: utf-8 -*-
import random
import socket
import sys
import os
import time
from typing import Optional, Union

from udp import Connection
from udp import Gate, GateDelegate, GateStatus
from udp import Hub, ClientHub
from udp import Arrival, Departure

from tcp import PlainArrival, PlainDeparture

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

from stun import Client

from tests.stargate import UDPGate


class StunClient(Client, GateDelegate):

    def __init__(self, host: str, port: int):
        super().__init__(host=host, port=port)
        self.__cargoes = []
        gate = UDPGate(delegate=self)
        gate.hub = ClientHub(delegate=gate)
        self.__gate = gate

    @property
    def gate(self) -> UDPGate:
        return self.__gate

    @property
    def hub(self) -> ClientHub:
        return self.gate.hub

    def start(self):
        self.hub.bind(address=self.source_address)
        self.gate.start()

    def stop(self):
        self.gate.stop()

    #
    #   Gate Delegate
    #

    # Override
    def gate_status_changed(self, previous: GateStatus, current: GateStatus,
                            remote: tuple, local: Optional[tuple], gate: Gate):
        UDPGate.info('!!! connection (%s, %s) state changed: %s -> %s' % (remote, local, previous, current))

    # Override
    def gate_received(self, ship: Arrival,
                      source: tuple, destination: Optional[tuple], connection: Connection):
        assert isinstance(ship, PlainArrival), 'arrival ship error: %s' % ship
        data = ship.package
        if not isinstance(data, bytes) or len(data) == 0:
            # should not happen
            return None
        self.__cargoes.append((data, source))

    # Override
    def gate_sent(self, ship: Departure,
                  source: Optional[tuple], destination: tuple, connection: Connection):
        assert isinstance(ship, PlainDeparture), 'departure ship error: %s' % ship
        data = ship.package
        size = len(data)
        UDPGate.info('message sent: %d byte(s) to %s' % (size, destination))

    # Override
    def gate_error(self, error, ship: Departure,
                   source: Optional[tuple], destination: tuple, connection: Connection):
        UDPGate.error('gate error (%s, %s): %s' % (source, destination, error))

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
            elif time.time() > expired:
                # timeout
                break
            else:
                time.sleep(0.25)
        if data is not None:
            self.info('received %d byte(s) from %s' % (len(data), remote))
        return data, remote

    # Override
    def send(self, data: bytes, destination: tuple, source: Union[tuple, int] = None) -> bool:
        if source is None:
            source = self.source_address
        elif isinstance(source, int):
            source = (self.source_address[0], source)
        try:
            self.gate.send_data(payload=data, source=source, destination=destination)
            return True
        except socket.error:
            return False

    # Override
    def info(self, msg: str):
        UDPGate.info(msg=msg)

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

    (SERVER_TEST, 3478),
    # (SERVER_GZ1, 3478),
    # (SERVER_GZ2, 3478),
    # (SERVER_HK2, 3478),

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
]

LOCAL_IP = Hub.inet_address()
LOCAL_PORT = random.choice(range(19900, 19999))


if __name__ == '__main__':

    g_client = StunClient(host=LOCAL_IP, port=LOCAL_PORT)

    g_client.start()

    print('================================================================')
    print('== Local Address: (%s:%d)' % (LOCAL_IP, LOCAL_PORT))
    # create client
    for address in STUN_SERVERS:
        g_client.detect(stun_host=address[0], stun_port=address[1])
    # exit
    print('== Local Address: (%s:%d)' % (LOCAL_IP, LOCAL_PORT))
    print('================================================================')

    g_client.stop()
