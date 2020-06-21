#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

from tests.node import Node
from tests.config import SERVER_HOST, SERVER_PORT


class Server(Node):
    pass


if __name__ == '__main__':

    # create server
    print('UDP server (%s:%d) starting ...' % (SERVER_HOST, SERVER_PORT))
    g_server = Server(host=SERVER_HOST, port=SERVER_PORT)
