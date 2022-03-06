# -*- coding: utf-8 -*-
#
#   UDP: User Datagram Protocol
#
#                                Written in 2020 by Moky <albert.moky@gmail.com>
#
# ==============================================================================
# MIT License
#
# Copyright (c) 2020 Albert Moky
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
from typing import Optional

from startrek.types import Address
from startrek.net.channel import is_opened, is_bound, is_connected
from startrek import BaseChannel, ChannelReader, ChannelWriter


class PackageChannelReader(ChannelReader):

    def _try_receive(self, max_len: int, sock: socket.socket) -> (Optional[bytes], Optional[Address]):
        try:
            return sock.recvfrom(max_len)
        except socket.error as error:
            error = self._check_error(error=error, sock=sock)
            if error is not None:
                # connection lost?
                raise error
            # received nothing
            return None, None

    def _receive_from(self, max_len: int) -> (Optional[bytes], Optional[Address]):
        sock = self.sock
        data, remote = self._try_receive(max_len=max_len, sock=sock)
        # check data
        error = self._check_data(data=data, sock=sock)
        if error is not None:
            # connection lost!
            raise error
        # OK
        return data, remote

    # Override
    def receive(self, max_len: int) -> (Optional[bytes], Optional[Address]):
        remote = self.remote_address
        if remote is None:
            # not connect (UDP)
            return self._receive_from(max_len=max_len)
        else:
            # connected (TCP/UDP)
            return self.read(max_len=max_len), remote


class PackageChannelWriter(ChannelWriter):

    def _try_send(self, data: bytes, target: Address, sock: socket.socket) -> int:
        try:
            return sock.sendto(data, target)
        except socket.error as error:
            error = self._check_error(error=error)
            if error is None:
                # buffer overflow!
                return -1
            else:
                # connection lost?
                raise error

    # Override
    def send(self, data: bytes, target: Address) -> int:
        remote = self.remote_address
        if remote is None:
            # not connect (UDP)
            return self._try_send(data=data, target=target, sock=self.sock)
        else:
            # connected (TCP/UDP)
            assert target is None or target == remote, 'target address error: %s, %s' % (target, remote)
            # return sock.send(data)
            return self._try_write(data=data, sock=self.sock)


class PackageChannel(BaseChannel):
    """ Discrete Package Channel """

    def __init__(self, remote: Optional[Address], local: Optional[Address], sock: socket.socket):
        super().__init__(remote=remote, local=local)
        self.__sock = sock
        self._refresh_flags(sock=sock)

    # Override
    def _get_socket(self) -> Optional[socket.socket]:
        return self.__sock

    # Override
    def _set_socket(self, sock: Optional[socket.socket]):
        # 1. replace old socket
        old = self.__sock
        self.__sock = sock
        self._refresh_flags(sock=sock)
        # 2. close old socket
        if old is not None and old is not sock:
            if is_opened(sock=old) and is_connected(sock=old):
                # DON'T close bound socket
                close_socket(sock=old)

    # Override
    def disconnect(self) -> Optional[socket.socket]:
        # DON'T close bound socket channel
        if self.bound and not self.connected:
            return None
        return super().disconnect()

    # Override
    def close(self):
        # DON'T close bound socket channel
        if self.bound and not self.connected:
            return False
        super().close()

    # Override
    def _create_reader(self):
        return PackageChannelReader(channel=self)

    # Override
    def _create_writer(self):
        return PackageChannelWriter(channel=self)


def close_socket(sock: socket.socket):
    # DON'T close bound socket
    if is_bound(sock=sock) and not is_connected(sock=sock):
        return False
    try:
        # sock.shutdown(socket.SHUT_RDWR)
        sock.close()
    except socket.error as error:
        print('[UDP] failed to close socket: %s, %s' % (error, sock))
