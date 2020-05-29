#! /usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QApplication

import udp
import stun

import sys
import os

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

from chat.client import STUNClient, DMTPClient
from chat.ui import Window


"""
    Config
"""

SERVER_GZ1 = '134.175.87.98'
SERVER_GZ2 = '203.195.224.155'
SERVER_GZ3 = '129.204.94.164'

# STUN_SERVER_HOST = '127.0.0.1'
STUN_SERVER_HOST = SERVER_GZ1
STUN_SERVER_PORT = 3478

# DMTP_SERVER_HOST = '127.0.0.1'
DMTP_SERVER_HOST = SERVER_GZ1
DMTP_SERVER_PORT = 9395

CLIENT_HOST = stun.Client.get_local_ip()
CLIENT_PORT = 9527  # random.choice(range(9900, 9999))


# create a hub for sockets
g_hub = udp.Hub()
g_hub.open(host=CLIENT_HOST, port=CLIENT_PORT)
g_hub.start()


"""
    STUN
"""

# STUN client
g_stun_client = client = STUNClient(hub=g_hub)
g_stun_client.source_address = (CLIENT_HOST, CLIENT_PORT)
g_stun_client.server_address = (STUN_SERVER_HOST, STUN_SERVER_PORT)


"""
    DMTP
"""

# DMTP client
g_dmtp_client = DMTPClient(hub=g_hub)
g_dmtp_client.source_address = (CLIENT_HOST, CLIENT_PORT)
g_dmtp_client.server_address = (DMTP_SERVER_HOST, DMTP_SERVER_PORT)


if __name__ == '__main__':
    # create App
    app = QApplication(sys.argv)

    window = Window(dmtp_client=g_dmtp_client, stun_client=g_stun_client)
    window.show()

    sys.exit(app.exec_())
