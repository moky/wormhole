#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import sys
import os
import traceback

import dmtp

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

from tests.database import ContactManager, FieldValueEncoder


SERVER_HOST = '0.0.0.0'
SERVER_PORT = 9395


class Server(dmtp.Server):

    def __init__(self, port: int, host: str='127.0.0.1'):
        super().__init__(local_address=(host, port))
        # database for location of contacts
        db = self._create_contact_manager()
        db.identifier = 'station@anywhere'
        self.__database = db
        self.delegate = db

    def _create_contact_manager(self) -> ContactManager:
        db = ContactManager(peer=self.peer)
        db.identifier = 'station@anywhere'
        return db

    @property
    def identifier(self) -> str:
        return self.__database.identifier

    @identifier.setter
    def identifier(self, value: str):
        self.__database.identifier = value

    def process_command(self, cmd: dmtp.Command, source: tuple) -> bool:
        print('received cmd from %s:\n\t%s' % (source, cmd))
        # noinspection PyBroadException
        try:
            return super().process_command(cmd=cmd, source=source)
        except Exception:
            traceback.print_exc()
            return False

    def process_message(self, msg: dmtp.Message, source: tuple) -> bool:
        print('received msg from %s:\n\t%s' % (source, json.dumps(msg, cls=FieldValueEncoder)))
        # return super().process_message(msg=msg, source=source)
        return True

    def send_command(self, cmd: dmtp.Command, destination: tuple) -> dmtp.Departure:
        print('sending cmd to %s:\n\t%s' % (destination, cmd))
        return super().send_command(cmd=cmd, destination=destination)

    def send_message(self, msg: dmtp.Message, destination: tuple) -> dmtp.Departure:
        print('sending msg to %s:\n\t%s' % (destination, json.dumps(msg, cls=FieldValueEncoder)))
        return super().send_message(msg=msg, destination=destination)

    #
    #   Server actions
    #

    def say_hello(self, destination: tuple) -> bool:
        if super().say_hello(destination=destination):
            return True
        cmd = dmtp.HelloCommand.new(identifier=self.identifier)
        self.send_command(cmd=cmd, destination=destination)
        return True


if __name__ == '__main__':

    print('UDP server (%s:%d) starting ...' % (SERVER_HOST, SERVER_PORT))

    # create server
    g_server = Server(host=SERVER_HOST, port=SERVER_PORT)
    g_server.start()
