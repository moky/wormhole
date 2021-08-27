#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import socket
import sys
import os
import threading
import time
import traceback
from typing import Optional, Dict

from udp.ba import ByteArray, Data
from udp.mtp import Header
from udp import Channel, DiscreteChannel
from udp import Connection, ConnectionDelegate
from udp import Hub, PackageHub

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

import dmtp
from tests.manager import ContactManager, FieldValueEncoder


class ServerHub(PackageHub):

    def __init__(self, delegate: ConnectionDelegate):
        super().__init__(delegate=delegate)
        self.__connections: Dict[tuple, Connection] = {}
        self.__sockets: Dict[tuple, socket.socket] = {}
        self.__running = False

    @property
    def running(self) -> bool:
        return self.__running

    def start(self):
        self.__running = True

    def stop(self):
        self.__running = False

    def bind(self, local: tuple) -> Connection:
        sock = self.__sockets.get(local)
        if sock is None:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            sock.bind(local)
            sock.setblocking(False)
            self.__sockets[local] = sock
        return self.connect(remote=None, local=local)

    # Override
    def create_connection(self, remote: Optional[tuple], local: Optional[tuple]) -> Connection:
        conn = self.__connections.get(local)
        if conn is None:
            conn = super().create_connection(remote=None, local=local)
            self.__connections[local] = conn
        return conn

    # Override
    def create_channel(self, remote: Optional[tuple], local: Optional[tuple]) -> Channel:
        sock = self.__sockets.get(local)
        if sock is not None:
            return DiscreteChannel(sock=sock)
        else:
            raise LookupError('failed to get channel: %s -> %s' % (remote, local))


class Server(dmtp.Server, ConnectionDelegate):

    def __init__(self, host: str, port: int):
        super().__init__()
        self.__local_address = (host, port)
        self.__hub = ServerHub(delegate=self)
        self.__db: Optional[ContactManager] = None

    @property
    def hub(self) -> ServerHub:
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
    def connection_state_changed(self, connection: Connection, previous, current):
        self.info('!!! connection (%s, %s) state changed: %s -> %s'
                  % (connection.local_address, connection.remote_address, previous, current))

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
            self.error('failed to process command (%s): %s' % (cmd, error))
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
            self.error('failed to send command: %s' % error)

    # Override
    def send_message(self, msg: dmtp.Message, destination: tuple) -> bool:
        self.info('sending msg to %s:\n\t%s' % (destination, json.dumps(msg, cls=FieldValueEncoder)))
        try:
            body = msg.get_bytes()
            source = self.__local_address
            self.__hub.send_message(body=body, source=source, destination=destination)
            return True
        except socket.error as error:
            self.error('failed to send message: %s' % error)

    #
    #   Server actions
    #

    # Override
    def say_hello(self, destination: tuple) -> bool:
        if super().say_hello(destination=destination):
            return True
        cmd = dmtp.Command.hello_command(identifier=self.identifier)
        return self.send_command(cmd=cmd, destination=destination)

    def start(self):
        self.__hub.bind(local=self.__local_address)
        self.__hub.start()
        threading.Thread(target=self.run).start()

    def run(self):
        while self.__hub.running:
            self.__hub.tick()
            time.sleep(0.0078125)


SERVER_HOST = Hub.inet_address()
SERVER_PORT = 9395


if __name__ == '__main__':

    print('UDP server (%s:%d) starting ...' % (SERVER_HOST, SERVER_PORT))

    g_server = Server(host=SERVER_HOST, port=SERVER_PORT)

    # database for location of contacts
    server_address = (SERVER_HOST, SERVER_PORT)
    g_server.database = ContactManager(hub=g_server.hub, local=server_address)
    g_server.identifier = 'station@anywhere'
    g_server.delegate = g_server.database

    g_server.start()
