#! /usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional

import sys
import os

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

import udp
import dmtp


SERVER_HOST = '0.0.0.0'
SERVER_PORT = 9394

# create a hub for sockets
g_hub = udp.Hub()
g_hub.open(host=SERVER_HOST, port=SERVER_PORT)
g_hub.start()


class Server(dmtp.Server):

    def __init__(self, hub: udp.Hub):
        super().__init__(hub=hub)
        self.__locations = {}

    def set_location(self, value: dmtp.LocationValue) -> bool:
        if value.ip is None or value.port == 0:
            return False
        print('update location: %s' % value.to_dict())
        self.__locations[value.id] = value
        self.__locations[(value.ip, value.port)] = value
        return True

    def get_location(self, uid: str = None, source: tuple = None) -> Optional[dmtp.LocationValue]:
        if uid is None:
            return self.__locations.get(source)
        else:
            return self.__locations.get(uid)

    def process_message(self, msg: dmtp.Message, source: tuple) -> bool:
        print('received msg: %s' % msg.to_dict())
        return True


if __name__ == '__main__':
    # create server
    print('server (%s:%d) starting ...' % (SERVER_HOST, SERVER_PORT))
    server = Server(hub=g_hub)
