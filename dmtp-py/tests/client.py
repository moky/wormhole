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

from udp.ba import Data
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

    def create_channel(self, remote: Optional[tuple], local: Optional[tuple]) -> Channel:
        channel = DiscreteChannel(remote=remote, local=local)
        channel.configure_blocking(False)
        return channel


class Client(dmtp.Client, ConnectionDelegate):

    def __init__(self, host: str, port: int):
        super().__init__()
        self.__local_address = (host, port)
        self.__hub: Optional[ClientHub] = None
        self.__db: Optional[ContactManager] = None
        self.__running = False
        self.remote_address = None
        self.nat = 'Unknown'

    @property
    def local_address(self) -> tuple:
        return self.__local_address

    @property
    def hub(self) -> ClientHub:
        return self.__hub

    @hub.setter
    def hub(self, peer: ClientHub):
        self.__hub = peer

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
        print('> %s' % msg)

    def _connect(self, remote: tuple):
        try:
            self.hub.connect(remote=remote, local=self.local_address)
        except socket.error as error:
            self.info('failed to connect to %s: %s' % (remote, error))

    def run(self):
        remote = self.remote_address
        local = self.local_address
        try:
            self.hub.connect(remote=remote, local=local)
        except socket.error as error:
            self.info('failed to connect to %s: %s' % (remote, error))
        # running
        self.__running = True
        while self.__running:
            self.hub.tick()
            time.sleep(0.1)

    def connection_state_changing(self, connection: Connection, current_state, next_state):
        self.info('!!! connection (%s, %s) state changed: %s -> %s'
                  % (connection.local_address, connection.remote_address, current_state, next_state))

    def connection_data_received(self, connection: Connection, remote: tuple, wrapper, payload: bytes):
        if isinstance(wrapper, Header) and len(payload) > 0:
            body = Data(buffer=payload)
            self._received(head=wrapper, body=body, source=remote)

    def _process_command(self, cmd: dmtp.Command, source: tuple) -> bool:
        print('received cmd from %s:\n\t%s' % (source, cmd))
        # noinspection PyBroadException
        try:
            return super()._process_command(cmd=cmd, source=source)
        except Exception:
            traceback.print_exc()
            return False

    def _process_message(self, msg: dmtp.Message, source: tuple) -> bool:
        print('received msg from %s:\n\t%s' % (source, json.dumps(msg, cls=FieldValueEncoder)))
        # return super()._process_message(msg=msg, source=source)
        return True

    def send_command(self, cmd: dmtp.Command, destination: tuple) -> bool:
        print('sending cmd to %s:\n\t%s' % (destination, cmd))
        try:
            body = cmd.get_bytes()
            source = self.local_address
            self.hub.send_command(body=body, source=source, destination=destination)
            return True
        except socket.error as error:
            self.info('failed to send command: %s' % error)

    def send_message(self, msg: dmtp.Message, destination: tuple) -> bool:
        print('sending msg to %s:\n\t%s' % (destination, json.dumps(msg, cls=FieldValueEncoder)))
        try:
            body = msg.get_bytes()
            source = self.local_address
            self.hub.send_message(body=body, source=source, destination=destination)
            return True
        except socket.error as error:
            self.info('failed to send message: %s' % error)

    #
    #   Client actions
    #

    def say_hello(self, destination: tuple) -> bool:
        if super().say_hello(destination=destination):
            return True
        cmd = dmtp.Command.hello_command(identifier=self.identifier)
        print('send cmd: %s' % cmd)
        self.send_command(cmd=cmd, destination=destination)
        return True

    def call(self, identifier: str) -> bool:
        cmd = dmtp.Command.call_command(identifier=identifier)
        print('send cmd: %s' % cmd)
        self.send_command(cmd=cmd, destination=self.remote_address)
        return True

    def login(self, identifier: str, server_address: tuple):
        self.identifier = identifier
        self.remote_address = server_address
        self._connect(remote=server_address)
        self.say_hello(destination=server_address)

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
                conn = self.hub.connect(remote=source_address, local=None)
                if conn is not None:
                    if conn.state in [ConnectionState.CONNECTED, ConnectionState.MAINTAINING, ConnectionState.EXPIRED]:
                        sessions.append(Session(location=loc, address=source_address))
                        continue
            mapped_address = loc.mapped_address
            if mapped_address is not None:
                conn = self.hub.connect(remote=mapped_address, local=None)
                if conn is not None:
                    if conn.state in [ConnectionState.CONNECTED, ConnectionState.MAINTAINING, ConnectionState.EXPIRED]:
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
            print('send msg to %s:\n\t%s' % (item.address, msg))
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

    # create client
    g_client = Client(host=CLIENT_HOST, port=CLIENT_PORT)
    g_client.remote_address = (SERVER_HOST, SERVER_PORT)

    # client hub
    g_client.hub = ClientHub(delegate=g_client)

    # database for location of contacts
    g_client.database = ContactManager(hub=g_client.hub, local=g_client.local_address)
    g_client.identifier = user
    g_client.delegate = g_client.database

    # g_client.start()
    threading.Thread(target=g_client.run).start()

    g_client.login(identifier=user, server_address=(SERVER_HOST, SERVER_PORT))

    # test send
    text = '你好 %s！' % friend
    index = 0
    while True:
        time.sleep(5)
        print('---- [%d]' % index)
        g_client.send_text(receiver=friend, msg='%s (%d)' % (text, index))
        index += 1
