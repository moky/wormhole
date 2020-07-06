#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import random

import sys
import os
import time
from typing import Optional

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

import stun
import dmtp

from tests.contacts import ContactManager, Session


SERVER_GZ1 = '134.175.87.98'
SERVER_GZ2 = '203.195.224.155'
SERVER_GZ3 = '129.204.94.164'

# SERVER_HOST = '127.0.0.1'
SERVER_HOST = '192.168.31.64'
# SERVER_HOST = SERVER_GZ1
SERVER_PORT = 9395

CLIENT_HOST = stun.get_local_ip()
CLIENT_PORT = random.choice(range(9900, 9999))


class Client(dmtp.Client):

    def __init__(self, port: int, host: str='127.0.0.1'):
        super().__init__(local_address=(host, port))
        self.server_address = None
        self.identifier = 'moky-%d' % port
        self.nat = 'Port Restricted Cone NAT'

    def connect(self, remote_address: tuple) -> Optional[dmtp.Connection]:
        return self.peer.connect(remote_address=remote_address)

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
        self.send_command(cmd=cmd, destination=self.server_address)
        return True

    def process_command(self, cmd: dmtp.Command, source: tuple) -> bool:
        print('received cmd from %s:\n\t%s' % (source, cmd))
        return super().process_command(cmd=cmd, source=source)

    def process_message(self, msg: dmtp.Message, source: tuple) -> bool:
        print('received msg from %s:\n\t%s' % (source, msg))
        content = msg.content
        if content is not None:
            print('msg content: "%s"' % content)
        return super().process_message(msg=msg, source=source)

    def send_command(self, cmd: dmtp.Command, destination: tuple) -> dmtp.Departure:
        print('sending cmd to %s:\n\t%s' % (destination, cmd))
        return super().send_command(cmd=cmd, destination=destination)

    def send_message(self, msg: dmtp.Message, destination: tuple) -> dmtp.Departure:
        print('sending msg to %s:\n\t%s' % (destination, msg))
        return super().send_message(msg=msg, destination=destination)

    def get_sessions(self, identifier: str) -> list:
        """
        Get connected locations for user ID

        :param identifier: user ID
        :return: connected locations and addresses
        """
        assert self.delegate is not None, 'contact delegate not set'
        locations = self.delegate.get_locations(identifier=identifier)
        if len(locations) == 0:
            # locations not found
            return []
        sessions = []
        for loc in locations:
            assert isinstance(loc, dmtp.LocationValue), 'location error: %s' % loc
            if loc.source_address is not None:
                addr = loc.source_address
                if self.peer.is_connected(remote_address=addr):
                    sessions.append(Session(location=loc, address=addr))
                    continue
            if loc.mapped_address is not None:
                addr = loc.mapped_address
                if self.peer.is_connected(remote_address=addr):
                    sessions.append(Session(location=loc, address=addr))
                    continue
        return sessions

    def send_text(self, receiver: str, msg: str) -> bool:
        sessions = self.get_sessions(identifier=receiver)
        if len(sessions) == 0:
            print('user (%s) not login ...' % receiver)
            # ask the server to help building a connection
            self.call(identifier=receiver)
            return False
        content = msg.encode('utf-8')
        msg = dmtp.Message.new(info={
            'sender': g_client.identifier,
            'receiver': receiver,
            'time': int(time.time()),
            'data': content,
        })
        for item in sessions:
            assert isinstance(item, Session), 'session error: %s' % item
            print('sending msg to %s:\n\t%s' % (item.address, msg))
            self.send_message(msg=msg, destination=item.address)
        return True


if __name__ == '__main__':
    # create client
    print('UDP client %s -> %s starting ...' % ((CLIENT_HOST, CLIENT_PORT), (SERVER_HOST, SERVER_PORT)))
    g_client = Client(host=CLIENT_HOST, port=CLIENT_PORT)
    g_client.server_address = (SERVER_HOST, SERVER_PORT)

    g_database = ContactManager()
    g_database.identifier = g_client.identifier
    g_database.source_address = g_client.peer.local_address

    g_client.delegate = g_database
    g_client.start()

    friend = 'moky'

    if len(sys.argv) == 3:
        g_client.identifier = sys.argv[1]
        friend = sys.argv[2]

    # login
    g_client.connect(remote_address=g_client.server_address)
    g_client.say_hello(destination=g_client.server_address)

    # test send
    text = '你好 %s！' % friend
    index = 0
    while True:
        time.sleep(5)
        print('---- [%d]' % index)
        g_client.send_text(receiver=friend, msg='%s (%d)' % (text, index))
        index += 1
