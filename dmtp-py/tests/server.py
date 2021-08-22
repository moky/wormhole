#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import socket
import sys
import os
import time
import traceback
from typing import Optional

from udp.ba import Data
from udp.mtp import Header
from udp import Hub
from udp import Channel, Connection, ConnectionDelegate
from udp import DiscreteChannel, PackageHub

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

import dmtp
from tests.manager import ContactManager, FieldValueEncoder


class ServerHub(PackageHub):

    def __init__(self, delegate: ConnectionDelegate):
        super().__init__(delegate=delegate)
        self.__connection = None

    def bind(self, local: tuple) -> Connection:
        return self.connect(remote=None, local=local)

    def create_connection(self, remote: Optional[tuple], local: Optional[tuple]) -> Connection:
        if self.__connection is None:
            self.__connection = super().create_connection(remote=remote, local=local)
        return self.__connection

    def create_channel(self, remote: Optional[tuple], local: Optional[tuple]) -> Channel:
        sock = Server.master
        if sock is not None:
            return DiscreteChannel(sock=sock)


class Server(dmtp.Server, ConnectionDelegate):

    master: Optional[socket.socket] = None

    def __init__(self, host: str, port: int):
        super().__init__()
        self.__local_address = (host, port)
        self.__hub: Optional[ServerHub] = None
        self.__db: Optional[ContactManager] = None
        self.__running = False

    @property
    def local_address(self) -> tuple:
        return self.__local_address

    @property
    def hub(self) -> ServerHub:
        return self.__hub

    @hub.setter
    def hub(self, peer: ServerHub):
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

    def start(self):
        self.__running = True
        self.run()

    def run(self):
        local = self.local_address
        try:
            self.hub.bind(local=local)
        except socket.error as error:
            self.info('failed to bind to %s: %s' % (local, error))
        # running
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
    #   Server actions
    #

    def say_hello(self, destination: tuple) -> bool:
        if super().say_hello(destination=destination):
            return True
        cmd = dmtp.Command.hello_command(identifier=self.identifier)
        self.send_command(cmd=cmd, destination=destination)
        return True


SERVER_HOST = Hub.inet_address()
SERVER_PORT = 9395


if __name__ == '__main__':

    print('UDP server (%s:%d) starting ...' % (SERVER_HOST, SERVER_PORT))

    # create server
    g_server = Server(host=SERVER_HOST, port=SERVER_PORT)

    # server hub
    g_server.hub = ServerHub(delegate=g_server)

    # server socket
    Server.master = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    Server.master.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    Server.master.bind(g_server.local_address)
    Server.master.setblocking(False)

    # database for location of contacts
    g_server.database = ContactManager(hub=g_server.hub, local=g_server.local_address)
    g_server.identifier = 'station@anywhere'
    g_server.delegate = g_server.database

    g_server.start()
