#! /usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QApplication

import udp

import sys
import os

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

from chat.client import Client
from chat.ui import Window


def create_client(local_address: tuple, server_address: tuple):

    # create a hub for sockets
    hub = udp.Hub()
    hub.open(host=local_address[0], port=local_address[1])
    hub.connect(destination=server_address)
    hub.start()

    # create client
    print('UDP client %s -> %s starting ...' % (local_address, server_address))
    client = Client(hub=hub)
    client.server_address = server_address
    return client


SERVER_GZ1 = '134.175.87.98'
SERVER_GZ2 = '203.195.224.155'
SERVER_GZ3 = '129.204.94.164'

# SERVER_HOST = '127.0.0.1'
SERVER_HOST = SERVER_GZ1
SERVER_PORT = 9395

CLIENT_HOST = '0.0.0.0'
CLIENT_PORT = 9527  # random.choice(range(9900, 9999))


g_client = create_client(local_address=(CLIENT_HOST, CLIENT_PORT),
                         server_address=(SERVER_HOST, SERVER_PORT))


if __name__ == '__main__':
    app = QApplication(sys.argv)

    window = Window(client=g_client)
    window.show()

    sys.exit(app.exec_())
