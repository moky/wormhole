#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import random

from PyQt5.QtWidgets import QApplication

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

SERVER_TEST = '127.0.0.1'
SERVER_GZ1 = '134.175.87.98'
# SERVER_GZ2 = '203.195.224.155'

# STUN_SERVER_HOST = SERVER_TEST
STUN_SERVER_HOST = SERVER_GZ1
STUN_SERVER_PORT = 3478

# DMTP_SERVER_HOST = SERVER_TEST
DMTP_SERVER_HOST = SERVER_GZ1
DMTP_SERVER_PORT = 9395

CLIENT_HOST = stun.get_local_ip()
CLIENT_PORT = random.choice(range(9900, 9999))


"""
    STUN Client
"""

g_stun_client = client = STUNClient(host=CLIENT_HOST, port=CLIENT_PORT+100)
g_stun_client.server_address = (STUN_SERVER_HOST, STUN_SERVER_PORT)


"""
    DMTP Client
"""

g_dmtp_client = DMTPClient(host=CLIENT_HOST, port=CLIENT_PORT)
g_dmtp_client.server_address = (DMTP_SERVER_HOST, DMTP_SERVER_PORT)


if __name__ == '__main__':
    # create App
    app = QApplication(sys.argv)

    window = Window(dmtp_client=g_dmtp_client, stun_client=g_stun_client)
    window.show()

    sys.exit(app.exec_())
