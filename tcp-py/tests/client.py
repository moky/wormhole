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

from tcp import Connection, ConnectionDelegate, ConnectionState
from tcp import Channel, StreamChannel
from tcp import ActiveStreamHub

from tests.config import SERVER_HOST, SERVER_PORT


class ClientHub(ActiveStreamHub):

    def create_channel(self, remote: tuple, local: tuple) -> Channel:
        channel = StreamChannel(remote=remote, local=local)
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

    def run(self):
        text = ''
        for _ in range(1024):
            text += ' Hello!'
        for index in range(16):
            data = '%d sheep: %s' % (index, text)
            self.info('>>> sending (%d bytes): %s' % (len(data), data))
            data = data.encode('utf-8')
            self.__send(data=data, source=None, destination=self.remote_address)
            time.sleep(2)
            data = self.__receive(source=self.remote_address, destination=None)
            if data is not None:
                self.received_data(data=data, source=self.remote_address, destination=None)
        self.__disconnect(remote=self.remote_address, local=None)


if __name__ == '__main__':

    server_address = (SERVER_HOST, SERVER_PORT)
    print('Connecting server (%s) ...' % str(server_address))

    g_client = Client()

    Client.remote_address = server_address
    Client.hub = ClientHub(delegate=g_client)

    g_client.start()
