#! /usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Union

import sys
import os

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

import udp
import dmtp


SERVER_HOST = '0.0.0.0'
SERVER_PORT = 9395


class Server(dmtp.Server):

    def __init__(self, hub: udp.Hub):
        super().__init__()
        hub.add_listener(self.peer)
        self.__hub = hub

    def say_hi(self, destination: tuple) -> bool:
        cmd = dmtp.HelloCommand.new(identifier='station@anywhere')
        print('sending cmd: %s' % cmd)
        self.send_command(cmd=cmd, destination=destination)
        return True

    # noinspection PyMethodMayBeStatic
    def __analyze_location(self, location: dmtp.LocationValue) -> int:
        if location is None:
            return -1
        if location.identifier is None:
            # user ID error
            return -2
        if location.mapped_address is None:
            # address error
            return -3
        if location.signature is None:
            # not signed
            return -4
        # verify addresses and timestamp with signature
        timestamp = dmtp.TimestampValue(value=location.timestamp)
        data = location.mapped_address.data + timestamp.data
        if location.source_address is not None:
            # "source_address" + "mapped_address" + "time"
            data = location.source_address.data + data
        signature = location.signature
        # TODO: verify data and signature with public key
        assert data is not None and signature is not None
        return 0

    def set_location(self, location: dmtp.LocationValue) -> bool:
        if self.__analyze_location(location=location) < 0:
            print('location error: %s' % location)
            return False
        return super().set_location(location=location)

    def process_message(self, msg: dmtp.Message, source: tuple) -> bool:
        print('received msg: %s' % msg)
        return True

    #
    #   PeerDelegate
    #
    def send_data(self, data: bytes, destination: tuple, source: Union[tuple, int] = None) -> int:
        self.__hub.send(data=data, destination=destination, source=source)
        return 0


def create_udp_server(port: int, host='0.0.0.0') -> Server:
    # create a hub for sockets
    hub = udp.Hub()
    hub.open(host=host, port=port)
    hub.start()

    # create server
    print('UDP server (%s:%d) starting ...' % (host, port))
    return Server(hub=hub)


if __name__ == '__main__':
    g_server = create_udp_server(host=SERVER_HOST, port=SERVER_PORT)
