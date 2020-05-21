#! /usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional

import sys
import os

from dmtp import LocationValue

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

    def accept_login(self, value: LocationValue) -> bool:
        print('login accepted: %s' % value.to_dict())
        self.__locations[value.id] = value
        self.__locations[(value.ip, value.port)] = value
        return True

    def location(self, uid: str = None, source: tuple = None) -> Optional[LocationValue]:
        print('getting location: %s, %s' % (uid, source))
        if uid is None:
            return self.__locations[source]
        else:
            return self.__locations[uid]

    def process_message(self, msg: dmtp.Message, source: tuple, destination: tuple) -> bool:
        print('received msg: %s' % msg.to_dict())
        return True


if __name__ == '__main__':
    # create server
    server = Server(hub=g_hub)
