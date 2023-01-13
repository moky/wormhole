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
from typing import Optional, Tuple

from startrek.types import Address
from startrek import BaseChannel, ChannelReader, ChannelWriter


class PacketChannelReader(ChannelReader):
    """ Datagram Packet Channel Reader """

    def _try_receive(self, max_len: int, sock: socket.socket) -> Tuple[Optional[bytes], Optional[Address]]:
        try:
            return sock.recvfrom(max_len)
        except socket.error as error:
            error = self.check_error(error=error, sock=sock)
            if error is None:
                # received nothing
                return None, None
            else:
                # connection lost?
                raise error

    def _receive_from(self, max_len: int, sock: socket.socket) -> Tuple[Optional[bytes], Optional[Address]]:
        data, remote = self._try_receive(max_len=max_len, sock=sock)
        # check data
        error = self.check_data(data=data, sock=sock)
        if error is None:
            # OK
            return data, remote
        else:
            # connection lost!
            raise error

    # Override
    def receive(self, max_len: int) -> Tuple[Optional[bytes], Optional[Address]]:
        remote = self.remote_address
        if remote is None:
            # not connect (UDP)
            return self._receive_from(max_len=max_len, sock=self.sock)
        else:
            # connected (TCP/UDP)
            return self.read(max_len=max_len), remote


class PacketChannelWriter(ChannelWriter):
    """ Datagram Packet Channel Writer """

    def _try_send(self, data: bytes, target: Address, sock: socket.socket) -> int:
        try:
            return sock.sendto(data, target)
        except socket.error as error:
            error = self.check_error(error=error, sock=sock)
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
            assert target is not None, 'target missed for unbound channel'
            return self._try_send(data=data, target=target, sock=self.sock)
        else:
            # connected (TCP/UDP)
            remote = self.remote_address
            assert target is None or target == remote, 'target error: %s, remote=%s' % (target, remote)
            # return sock.send(data)
            return self._try_write(data=data, sock=self.sock)


class PacketChannel(BaseChannel):
    """ Datagram Packet Channel """

    # Override
    def _create_reader(self):
        return PacketChannelReader(channel=self)

    # Override
    def _create_writer(self):
        return PacketChannelWriter(channel=self)
