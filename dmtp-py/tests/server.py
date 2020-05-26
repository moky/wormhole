#! /usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional, Union

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
        self.__locations = {}

    @staticmethod
    def __analyze_location(location: dmtp.LocationValue) -> int:
        if location is None:
            return -1
        if location.id is None:
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

    def set_location(self, value: dmtp.LocationValue) -> bool:
        if self.__analyze_location(location=value) < 0:
            return False
        address = value.mapped_address
        self.__locations[value.id] = value
        self.__locations[(address.ip, address.port)] = value
        print('location updated: %s' % value)
        return True

    def get_location(self, uid: str = None, source: tuple = None) -> Optional[dmtp.LocationValue]:
        if uid is None:
            return self.__locations.get(source)
        else:
            return self.__locations.get(uid)

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
