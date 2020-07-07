#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import sys
import os

import dmtp

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

from tests.database import ContactManager


SERVER_HOST = '0.0.0.0'
SERVER_PORT = 9395


class Server(dmtp.Server):

    def __init__(self, port: int, host: str='127.0.0.1'):
        super().__init__(local_address=(host, port))
        self.__identifier = 'station@anywhere'
        self.__server_address = None
        self.nat = 'Unknown'
        # database for location of contacts
        db = self._create_contact_manager()
        self.__database = db
        self.delegate = db

    def _create_contact_manager(self) -> ContactManager:
        db = ContactManager(peer=self.peer)
        db.identifier = 'station@anywhere'
        return db

    def process_command(self, cmd: dmtp.Command, source: tuple) -> bool:
        print('received cmd: %s' % cmd)
        return super().process_command(cmd=cmd, source=source)

    def process_message(self, msg: dmtp.Message, source: tuple) -> bool:
        print('received msg: %s' % json.dumps(msg, cls=dmtp.FieldValueEncoder))
        return True


if __name__ == '__main__':

    print('UDP server (%s:%d) starting ...' % (SERVER_HOST, SERVER_PORT))

    # create server
    g_server = Server(host=SERVER_HOST, port=SERVER_PORT)
    g_server.start()
