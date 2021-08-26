#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import random
import socket
import sys
import os
import threading
import time
import traceback
from typing import Optional

from udp.ba import ByteArray, Data
from udp.mtp import Header
from udp import Hub
from udp import Channel, Connection, ConnectionDelegate, ConnectionState
from udp import DiscreteChannel, ActivePackageHub

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

import dmtp
from tests.manager import ContactManager, FieldValueEncoder, Session


SERVER_GZ1 = '134.175.87.98'
SERVER_GZ2 = '203.195.224.155'
SERVER_GZ3 = '129.204.94.164'

SERVER_HOST = Hub.inet_address()
SERVER_PORT = 9395

CLIENT_HOST = Hub.inet_address()
CLIENT_PORT = random.choice(range(9900, 9999))


class ClientHub(ActivePackageHub):

    # Override
    def create_channel(self, remote: Optional[tuple], local: Optional[tuple]) -> Channel:
        channel = DiscreteChannel(remote=remote, local=local)
        channel.configure_blocking(False)
        return channel


class Client(dmtp.Client, ConnectionDelegate):

    def __init__(self, local: tuple, remote: tuple):
        super().__init__()
        self.__local_address = local
        self.__remote_address = remote
        self.__hub = ClientHub(delegate=self)
        self.__db: Optional[ContactManager] = None
        self.__running = False

    @property
    def hub(self) -> ClientHub:
        return self.__hub

    @property
    def database(self) -> ContactManager:
        return self.__db

    @database.setter
    def database(self, db: ContactManager):
        self.__db = db

    @property
    def identifier(self) -> str:
        return self.__db.identifier

    @identifier.setter
    def identifier(self, uid: str):
        self.__db.identifier = uid

    # noinspection PyMethodMayBeStatic
    def info(self, msg: str):
        print('> ', msg)

    # noinspection PyMethodMayBeStatic
    def error(self, msg: str):
        print('ERROR> ', msg)

    # Override
    def _connect(self, remote: tuple):
        try:
            self.__hub.connect(remote=remote, local=self.__local_address)
        except socket.error as error:
            self.error('failed to connect to %s: %s' % (remote, error))

    # Override
    def connection_state_changing(self, connection: Connection, current_state, next_state):
        self.info('!!! connection (%s, %s) state changed: %s -> %s'
                  % (connection.local_address, connection.remote_address, current_state, next_state))

    # Override
    def connection_data_received(self, connection: Connection, remote: tuple, wrapper, payload: bytes):
        assert isinstance(wrapper, Header), 'Header error: %s' % wrapper
        if not isinstance(payload, ByteArray):
            payload = Data(buffer=payload)
        self._received(head=wrapper, body=payload, source=remote)

    # Override
    def _process_command(self, cmd: dmtp.Command, source: tuple) -> bool:
        self.info('received cmd from %s:\n\t%s' % (source, cmd))
        # noinspection PyBroadException
        try:
            return super()._process_command(cmd=cmd, source=source)
        except Exception as error:
            self.error('failed to process cmd: %s, %s' % (cmd, error))
            traceback.print_exc()
            return False

    # Override
    def _process_message(self, msg: dmtp.Message, source: tuple) -> bool:
        self.info('received msg from %s:\n\t%s' % (source, json.dumps(msg, cls=FieldValueEncoder)))
        # return super()._process_message(msg=msg, source=source)
        return True

    # Override
    def send_command(self, cmd: dmtp.Command, destination: tuple) -> bool:
        self.info('sending cmd to %s:\n\t%s' % (destination, cmd))
        try:
            body = cmd.get_bytes()
            source = self.__local_address
            self.__hub.send_command(body=body, source=source, destination=destination)
            return True
        except socket.error as error:
            self.error('failed to send cmd: %s' % error)

    # Override
    def send_message(self, msg: dmtp.Message, destination: tuple) -> bool:
        self.info('sending msg to %s:\n\t%s' % (destination, json.dumps(msg, cls=FieldValueEncoder)))
        try:
            body = msg.get_bytes()
            source = self.__local_address
            self.__hub.send_message(body=body, source=source, destination=destination)
            return True
        except socket.error as error:
            self.error('failed to send msg: %s' % error)

    #
    #   Client actions
    #

    # Override
    def say_hello(self, destination: tuple) -> bool:
        if super().say_hello(destination=destination):
            return True
        cmd = dmtp.Command.hello_command(identifier=self.identifier)
        self.info('send cmd: %s' % cmd)
        return self.send_command(cmd=cmd, destination=destination)

    def call(self, identifier: str) -> bool:
        cmd = dmtp.Command.call_command(identifier=identifier)
        self.info('send cmd: %s' % cmd)
        return self.send_command(cmd=cmd, destination=self.__remote_address)

    def login(self, identifier: str):
        self.identifier = identifier
        self._connect(remote=self.__remote_address)
        self.say_hello(destination=self.__remote_address)

    def get_sessions(self, identifier: str) -> list:
        """
        Get connected locations for user ID

        :param identifier: user ID
        :return: connected locations and addresses
        """
        sessions = []
        delegate = self.delegate
        assert delegate is not None, 'location delegate not set'
        locations = delegate.get_locations(identifier=identifier)
        for loc in locations:
            assert isinstance(loc, dmtp.LocationValue), 'location error: %s' % loc
            source_address = loc.source_address
            if source_address is not None:
                conn = self.__hub.connect(remote=source_address, local=None)
                if conn is not None:
                    if conn.state in [ConnectionState.CONNECTED, ConnectionState.MAINTAINING, ConnectionState.EXPIRED]:
                        sessions.append(Session(location=loc, address=source_address))
                        continue
            mapped_address = loc.mapped_address
            if mapped_address is not None:
                conn = self.__hub.connect(remote=mapped_address, local=None)
                if conn is not None:
                    if conn.state in [ConnectionState.CONNECTED, ConnectionState.MAINTAINING, ConnectionState.EXPIRED]:
                        sessions.append(Session(location=loc, address=mapped_address))
                        continue
        return sessions

    def send_text(self, receiver: str, msg: str) -> Optional[dmtp.Message]:
        sessions = self.get_sessions(identifier=receiver)
        if len(sessions) == 0:
            self.info('user (%s) not login ...' % receiver)
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
            self.info('send msg to %s:\n\t%s' % (item.address, msg))
            self.send_message(msg=msg, destination=item.address)
        return msg

    def start(self):
        self.__hub.connect(remote=self.__remote_address, local=self.__local_address)
        self.__running = True
        threading.Thread(target=self.run).start()

    def run(self):
        while self.__running:
            self.__hub.tick()
            time.sleep(0.1)


if __name__ == '__main__':

    user = 'moky-%d' % CLIENT_PORT
    friend = 'moky'

    if len(sys.argv) == 3:
        user = sys.argv[1]
        friend = sys.argv[2]

    # create client
    local_address = (CLIENT_HOST, CLIENT_PORT)
    remote_address = (SERVER_HOST, SERVER_PORT)
    print('UDP client %s -> %s starting ...' % (local_address, remote_address))
    g_client = Client(local=local_address, remote=remote_address)

    # database for location of contacts
    g_client.database = ContactManager(hub=g_client.hub, local=local_address)
    g_client.identifier = user
    g_client.delegate = g_client.database

    g_client.start()

    g_client.login(identifier=user)

    # test send
    text = '你好 %s！' % friend
    index = 0
    while True:
        time.sleep(5)
        print('---- [%d]' % index)
        g_client.send_text(receiver=friend, msg='%s (%d)' % (text, index))
        index += 1
