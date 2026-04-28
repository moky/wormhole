# -*- coding: utf-8 -*-
#
#   Star Trek: Interstellar Transport
#
#                                Written in 2026 by Moky <albert.moky@gmail.com>
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
from abc import ABC, abstractmethod
from typing import Optional, Tuple

from ..types import SocketAddress


class SocketReader(ABC):

    @abstractmethod
    async def read(self, max_len: int) -> Optional[bytes]:
        """ read data from socket """
        raise NotImplemented

    @abstractmethod
    async def receive(self, max_len: int) -> Tuple[Optional[bytes], Optional[SocketAddress]]:
        """ receive data via socket, and return it with remote address """
        raise NotImplemented


class SocketWriter(ABC):

    @abstractmethod
    async def write(self, data: bytes) -> int:
        """ write data into socket """
        raise NotImplemented

    @abstractmethod
    async def send(self, data: bytes, target: SocketAddress) -> int:
        """ send data via socket with remote address """
        raise NotImplemented


# noinspection PyMethodMayBeStatic
class SocketHelper:

    def get_local_address(self, sock: socket.socket) -> Optional[SocketAddress]:
        try:
            return sock.getsockname()
        except (OSError, socket.error):
            return None
        except Exception as error:
            print('[NET] unexpected error getting local address: %s' % error)
            return None

    def get_remote_address(self, sock: socket.socket) -> Optional[SocketAddress]:
        try:
            return sock.getpeername()
        except (OSError, socket.error):
            return None
        except Exception as error:
            print('[NET] unexpected error getting remote address: %s' % error)
            return None

    #
    #   Flags
    #

    def is_bound(self, sock: socket.socket) -> bool:
        address = self.get_local_address(sock=sock)
        return address is not None

    def is_connected(self, sock: socket.socket) -> bool:
        address = self.get_remote_address(sock=sock)
        return address is not None

    def is_closed(self, sock: socket.socket) -> bool:
        if hasattr(sock, '_closed'):
            return getattr(sock, '_closed', False)
        try:
            sock.fileno()
            return False
        except (OSError, socket.error):
            return True
        except Exception as error:
            print('[NET] unexpected error checking socket closed: %s' % error)
            return True

    def is_available(self, sock: socket.socket) -> bool:
        """ Ready for reading """
        try:
            ready, _, _ = select.select([sock], [], [], 0)
            return sock in ready
        except (OSError, ValueError):
            return False
        except Exception as error:
            print('[NET] unexpected error checking available: %s' % error)
            return False

    def is_vacant(self, sock: socket.socket) -> bool:
        """ Ready for writing """
        try:
            _, ready, _ = select.select([], [sock], [], 0)
            return sock in ready
        except (OSError, ValueError):
            return False
        except Exception as error:
            print('[NET] unexpected error checking vacant: %s' % error)
            return False

    def is_blocking(self, sock: socket.socket) -> bool:
        try:
            return sock.getblocking()
        except (OSError, socket.error):
            return False
        except Exception as error:
            print('[NET] unexpected error getting blocking: %s' % error)
            return False

    #
    #   Sync
    #

    def set_blocking(self, sock: socket.socket, blocking: bool):
        try:
            sock.setblocking(blocking)
        except (OSError, socket.error):
            pass
        except Exception as error:
            print('[NET] unexpected error setting blocking: %s' % error)

    def bind(self, sock: socket.socket, local: SocketAddress) -> bool:
        """ Bind to local address """
        try:
            # TODO: async api
            sock.bind(local)
            return self.is_bound(sock=sock)
        # except (OSError, socket.error):
        #     return False
        except Exception as error:
            print('[Socket] cannot bind to: %s, socket: %s, %s' % (local, sock, error))
            return False

    #
    #   Async
    #

    async def connect(self, sock: socket.socket, remote: SocketAddress) -> bool:
        """ Connect to remote address """
        loop = asyncio.get_event_loop()
        try:
            await loop.sock_connect(sock, remote)
            # sock.connect(remote)
            # return not self.is_connected(sock=sock)
            return True
        # except (OSError, socket.error):
        #     return False
        except Exception as error:
            print('[Socket] cannot connect to: %s, socket: %s, %s' % (remote, sock, error))
            traceback.print_exc()
            try:
                sock.close()
            except (OSError, socket.error):
                pass
            return False

    async def disconnect(self, sock: socket.socket) -> bool:
        """ Close socket """
        if self.is_closed(sock=sock):
            return True
        try:
            # TODO: check for UDP socket
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except (OSError, socket.error):
                pass
            sock.close()
            # return not self.is_connected(sock=sock)
            return True
        # except (OSError, socket.error):
        #     return False
        except Exception as error:
            print('[Socket] cannot close socket: %s, %s' % (sock, error))
            traceback.print_exc()
            return False

    async def send(self, sock: socket.socket, data: bytes) -> int:
        """ Send data """
        # return sock.send(data)
        loop = asyncio.get_event_loop()
        try:
            await loop.sock_sendall(sock, data)
            return len(data)
        # except BlockingIOError:
        #     await asyncio.sleep(0.01)
        #     raise
        except OSError:
            raise
        except Exception as error:
            raise OSError('Failed to send data: %s' % error)

    async def receive(self, sock: socket.socket, max_len: int) -> Optional[bytes]:
        """ Receive data """
        # return sock.recv(max_len)
        loop = asyncio.get_event_loop()
        try:
            return await loop.sock_recv(sock, max_len)
        # except BlockingIOError:
        #     await asyncio.sleep(0.01)
        #     raise
        except OSError:
            raise
        except Exception as error:
            raise OSError('Failed to receive data: %s' % error)
