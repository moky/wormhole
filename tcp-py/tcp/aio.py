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

import asyncio
import select
import socket
import traceback
from typing import Optional

from startrek.types import SocketAddress


"""
    Async Socket I/O
    ~~~~~~~~~~~~~~~~
"""


async def get_local_address(sock: socket.socket) -> Optional[SocketAddress]:
    try:
        # TODO: async api
        return sock.getsockname()
    except socket.error:
        # print('[NET] failed to get local address: %s' % error)
        return None


async def get_remote_address(sock: socket.socket) -> Optional[SocketAddress]:
    try:
        # TODO: async api
        return sock.getpeername()
    except socket.error:
        # print('[NET] failed to get remote address: %s' % error)
        return None


#
#   Flags
#


async def is_blocking(sock: socket.socket) -> bool:
    try:
        # TODO: async api
        return sock.getblocking()
    except socket.error:
        # print('[NET] failed to get blocking: %s' % error)
        return False


async def is_bound(sock: socket.socket) -> bool:
    local = await get_local_address(sock=sock)
    return local is not None


async def is_connected(sock: socket.socket) -> bool:
    remote = await get_remote_address(sock=sock)
    return remote is not None


async def is_closed(sock: socket.socket) -> bool:
    # TODO: async api
    return getattr(sock, '_closed', False)


async def is_available(sock: socket.socket) -> bool:
    """ Ready for reading """
    ready, _, _ = select.select([sock], [], [], 0)
    return sock in ready


async def is_vacant(sock: socket.socket) -> bool:
    """ Ready for writing """
    _, ready, _ = select.select([], [sock], [], 0)
    return sock in ready


#
#   Flags
#


async def socket_send(sock: socket.socket, data: bytes) -> int:
    """ Send data """
    # return sock.send(data)
    loop = asyncio.get_event_loop()
    await loop.sock_sendall(sock=sock, data=data)
    return len(data)


async def socket_receive(sock: socket.socket, max_len: int) -> Optional[bytes]:
    """ Receive data """
    # return sock.recv(max_len)
    loop = asyncio.get_event_loop()
    return await loop.sock_recv(sock, max_len)


async def socket_bind(sock: socket.socket, local: SocketAddress) -> bool:
    """ Bind to local address """
    try:
        # TODO: async api
        sock.bind(local)
        return await is_bound(sock=sock)
    except socket.error as error:
        print('[Socket] cannot bind to: %s, socket: %s, %s' % (local, sock, error))
        traceback.print_exc()
        return False


async def socket_connect(sock: socket.socket, remote: SocketAddress) -> bool:
    """ Connect to remote address """
    try:
        if await is_blocking(sock=sock):
            sock.connect(remote)
        else:
            loop = asyncio.get_event_loop()
            await loop.sock_connect(sock, remote)
        return await is_connected(sock=sock)
    except socket.error as error:
        print('[Socket] cannot connect to: %s, socket: %s, %s' % (remote, sock, error))
        traceback.print_exc()
        return False


async def socket_disconnect(sock: socket.socket) -> bool:
    """ Close socket """
    if await is_closed(sock=sock) or not await is_connected(sock=sock):
        return True
    try:
        # TODO: check for UDP socket
        # sock.shutdown(socket.SHUT_RDWR)
        # TODO: async api
        sock.close()
        return not await is_connected(sock=sock)
    except socket.error as error:
        print('[Socket] cannot close socket: %s, %s' % (sock, error))
        traceback.print_exc()
        return False
