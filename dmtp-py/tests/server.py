#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

import dmtp

from tests.contacts import ContactManager


SERVER_HOST = '0.0.0.0'
SERVER_PORT = 9395


class Server(dmtp.Server):

    def __init__(self, port: int, host: str='127.0.0.1'):
        super().__init__(local_address=(host, port))
        self.identifier = 'station@anywhere'

    def process_command(self, cmd: dmtp.Command, source: tuple) -> bool:
        print('received cmd: %s' % cmd)
        return super().process_command(cmd=cmd, source=source)

    def process_message(self, msg: dmtp.Message, source: tuple) -> bool:
        print('received msg: %s' % msg)
        return True


if __name__ == '__main__':
    # create server
    print('UDP server (%s:%d) starting ...' % (SERVER_HOST, SERVER_PORT))
    g_server = Server(host=SERVER_HOST, port=SERVER_PORT)

    g_database = ContactManager()
    g_database.identifier = g_server.identifier
    g_database.source_address = g_server.peer.local_address

    g_server.delegate = g_database
    g_server.start()
