# -*- coding: utf-8 -*-
#
#   Star Trek: Interstellar Transport
#
#                                Written in 2021 by Moky <albert.moky@gmail.com>
#
# ==============================================================================
# MIT License
#
# Copyright (c) 2021 Albert Moky
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ==============================================================================

import socket
import traceback
from typing import Optional

from ..types import SocketAddress


"""
    Sync Socket I/O
    ~~~~~~~~~~~~~~~
"""


def get_local_address(sock: socket.socket) -> Optional[SocketAddress]:
    try:
        return sock.getsockname()
    except socket.error:
        # print('[NET] failed to get local address: %s' % error)
        return None


def get_remote_address(sock: socket.socket) -> Optional[SocketAddress]:
    try:
        return sock.getpeername()
    except socket.error:
        # print('[NET] failed to get remote address: %s' % error)
        return None


def is_blocking(sock: socket.socket) -> bool:
    try:
        return sock.getblocking()
    except socket.error:
        # print('[NET] failed to get blocking: %s' % error)
        return False


def is_connected(sock: socket.socket) -> bool:
    return get_remote_address(sock=sock) is not None


def is_bound(sock: socket.socket) -> bool:
    return get_local_address(sock=sock) is not None


def is_closed(sock: socket.socket) -> bool:
    return getattr(sock, '_closed', False)


def bind_socket(sock: socket.socket, local: SocketAddress) -> bool:
    """ Bind to local address """
    try:
        sock.bind(local)
        return is_bound(sock=sock)
    except socket.error as error:
        print('[Socket] cannot bind to: %s, socket: %s, %s' % (local, sock, error))
        traceback.print_exc()
        return False


def connect_socket(sock: socket.socket, remote: SocketAddress) -> bool:
    """ Connect to remote address """
    try:
        sock.connect(remote)
        return is_connected(sock=sock)
    except socket.error as error:
        print('[Socket] cannot connect to: %s, socket: %s, %s' % (remote, sock, error))
        traceback.print_exc()
        return False


def disconnect_socket(sock: socket.socket) -> bool:
    """ Close socket """
    if is_closed(sock=sock) or not is_connected(sock=sock):
        return True
    try:
        # TODO: check for UDP socket
        # sock.shutdown(socket.SHUT_RDWR)
        sock.close()
        return not is_connected(sock=sock)
    except socket.error as error:
        print('[Socket] cannot close socket: %s, %s' % (sock, error))
        traceback.print_exc()
        return False
