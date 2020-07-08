#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import random

import sys
import os
import time
from typing import Optional

import dmtp
import stun

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

from tests.database import ContactManager, FieldValueEncoder


SERVER_GZ1 = '134.175.87.98'
SERVER_GZ2 = '203.195.224.155'
SERVER_GZ3 = '129.204.94.164'

# SERVER_HOST = '127.0.0.1'
# SERVER_HOST = '192.168.31.64'
SERVER_HOST = SERVER_GZ1
SERVER_PORT = 9395

CLIENT_HOST = stun.get_local_ip()
CLIENT_PORT = random.choice(range(9900, 9999))


class Session:

    def __init__(self, location: dmtp.LocationValue, address: tuple):
        super().__init__()
        self.__location = location
        self.__address = address

    @property
    def location(self) -> dmtp.LocationValue:
        return self.__location

    @property
    def address(self) -> tuple:
        return self.__address


class Client(dmtp.Client):

    def __init__(self, port: int, host: str='127.0.0.1'):
        super().__init__(local_address=(host, port))
        self.__server_address = None
        self.nat = 'Unknown'
        # database for location of contacts
        db = self._create_contact_manager()
        db.identifier = 'moky-%d' % port
        self.__database = db
        self.delegate = db

    def _create_contact_manager(self) -> ContactManager:
        db = ContactManager(peer=self.peer)
        db.identifier = 'anyone@anywhere'
        return db

    @property
    def identifier(self) -> str:
        return self.__database.identifier

    def process_command(self, cmd: dmtp.Command, source: tuple) -> bool:
        print('received cmd from %s:\n\t%s' % (source, cmd))
        return super().process_command(cmd=cmd, source=source)

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

    def say_hello(self, destination: tuple) -> bool:
        if super().say_hello(destination=destination):
            return True
        cmd = dmtp.HelloCommand.new(identifier=self.identifier)
        print('send cmd: %s' % cmd)
        self.send_command(cmd=cmd, destination=destination)
        return True

    def call(self, identifier: str) -> bool:
        cmd = dmtp.CallCommand.new(identifier=identifier)
        print('sending cmd: %s' % cmd)
        self.send_command(cmd=cmd, destination=self.__server_address)
        return True

    def login(self, identifier: str, server_address: tuple):
        self.__database.identifier = identifier
        self.__server_address = server_address
        self.peer.connect(remote_address=server_address)
        self.say_hello(destination=server_address)

    def get_sessions(self, identifier: str) -> list:
        """
        Get connected locations for user ID

        :param identifier: user ID
        :return: connected locations and addresses
        """
        sessions = []
        assert self.delegate is not None, 'location delegate not set'
        locations = self.delegate.get_locations(identifier=identifier)
        now = int(time.time())
        for loc in locations:
            assert isinstance(loc, dmtp.LocationValue), 'location error: %s' % loc
            source_address = loc.source_address
            if source_address is not None:
                conn = self.peer.get_connection(remote_address=source_address)
                if conn is not None and conn.is_connected(now=now):
                    sessions.append(Session(location=loc, address=source_address))
                    continue
            mapped_address = loc.mapped_address
            if mapped_address is not None:
                conn = self.peer.get_connection(remote_address=mapped_address)
                if conn is not None and conn.is_connected(now=now):
                    sessions.append(Session(location=loc, address=mapped_address))
                    continue
        return sessions

    def send_text(self, receiver: str, msg: str) -> Optional[dmtp.Message]:
        sessions = self.get_sessions(identifier=receiver)
        if len(sessions) == 0:
            print('user (%s) not login ...' % receiver)
            # ask the server to help building a connection
            self.call(identifier=receiver)
            return None
        content = msg.encode('utf-8')
        msg = dmtp.Message.new(info={
            'sender': self.identifier,
            'receiver': receiver,
            'time': int(time.time()),
            'data': content,
        })
        for item in sessions:
            assert isinstance(item, Session), 'session error: %s' % item
            print('sending msg to %s:\n\t%s' % (item.address, msg))
            self.send_message(msg=msg, destination=item.address)
        return msg


if __name__ == '__main__':
    # create client
    print('UDP client %s -> %s starting ...' % ((CLIENT_HOST, CLIENT_PORT), (SERVER_HOST, SERVER_PORT)))

    user = 'moky-%d' % CLIENT_PORT
    friend = 'moky'

    if len(sys.argv) == 3:
        user = sys.argv[1]
        friend = sys.argv[2]

    g_client = Client(host=CLIENT_HOST, port=CLIENT_PORT)
    g_client.start()

    g_client.login(identifier=user, server_address=(SERVER_HOST, SERVER_PORT))

    # test send
    text = '你好 %s！' % friend
    index = 0
    while True:
        time.sleep(5)
        print('---- [%d]' % index)
        g_client.send_text(receiver=friend, msg='%s (%d)' % (text, index))
        index += 1
