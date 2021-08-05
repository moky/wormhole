#! /usr/bin/env python3
# -*- coding: utf-8 -*-
import socket
import threading
import time

import sys
import os
from typing import Optional

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

from udp.ba import Data
from udp.mtp import DataType, Package
from udp import Channel, Connection, ConnectionDelegate, ConnectionState
from udp import ActivePackageHub, DiscreteChannel

from tests.config import SERVER_HOST, SERVER_PORT, CLIENT_HOST, CLIENT_PORT


class ClientHub(ActivePackageHub):

    def create_channel(self, remote: tuple, local: Optional[tuple] = None) -> Channel:
        channel = DiscreteChannel(remote=remote, local=local)
        channel.configure_blocking(False)
        return channel


class Client(threading.Thread, ConnectionDelegate):

    remote_address: tuple = None

    hub: ClientHub = None

    # noinspection PyMethodMayBeStatic
    def info(self, msg: str):
        print('> %s' % msg)

    def connection_state_changing(self, connection: Connection, current_state, next_state):
        self.info('!!! connection (%s, %s) state changed: %s -> %s'
                  % (connection.local_address, connection.remote_address, current_state, next_state))
        if next_state == ConnectionState.EXPIRED:
            self.__heartbeat(connection=connection)

    def __heartbeat(self, connection: Connection):
        pass

    def received_data(self, data: bytes, source: tuple, destination: Optional[tuple]):
        text = data.decode('utf-8')
        self.info('<<< received (%d bytes) from %s to %s: %s'
                  % (len(data), source, destination, text))

    def __receive(self, source: tuple, destination: Optional[tuple]) -> bytes:
        try:
            return self.hub.receive(source=source, destination=destination)
        except socket.error as error:
            print('Server error: %s' % error)

    def __send(self, data: bytes, source: Optional[tuple], destination: tuple) -> bool:
        return self.hub.send(data=data, source=source, destination=destination)

    def __disconnect(self, remote: tuple, local: Optional[tuple]):
        self.hub.disconnect(remote=remote, local=local)

    def send_cmd(self, cmd: str):
        data = cmd.encode('utf-8')
        data = Data(data=data)
        address = self.remote_address
        print('sending cmd (%d bytes): "%s" to %s' % (data.size, cmd, address))
        pack = Package.new(data_type=DataType.COMMAND, body=data)
        return self.hub.send_package(pack=pack, source=None, destination=address)

    def send_msg(self, msg: str):
        data = msg.encode('utf-8')
        data = Data(data=data)
        address = self.remote_address
        print('sending msg (%d bytes): "%s" to %s' % (data.size, msg, address))
        pack = Package.new(data_type=DataType.MESSAGE, body=data)
        return self.hub.send_package(pack=pack, source=None, destination=address)

    def run(self):
        text = ''
        for _ in range(1024):
            text += ' Hello!'
        # test send
        for i in range(0, 32, 2):
            g_client.send_cmd(cmd='%d sheep:%s' % (i, text))
            g_client.send_msg(msg='%d sheep:%s' % (i+1, text))
            time.sleep(2)


if __name__ == '__main__':

    local_address = (CLIENT_HOST, CLIENT_PORT)
    server_address = (SERVER_HOST, SERVER_PORT)
    print('UDP client %s -> %s starting ...' % (local_address, server_address))

    # create client
    g_client = Client()

    Client.remote_address = server_address
    Client.hub = ClientHub(delegate=g_client)

    g_client.start()
