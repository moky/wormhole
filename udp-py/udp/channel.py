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

from startrek import BaseChannel


class PackageChannel(BaseChannel):
    """ Discrete Package Channel """

    def _receive_from(self, max_len: int) -> (Optional[bytes], Optional[tuple]):
        # check socket first
        sock = self.sock
        if sock is None:
            raise socket.error('socket lost, cannot read data')
        # try to receive data
        try:
            data, remote = sock.recvfrom(max_len)
        except socket.error as error:
            error = self._check_socket_error(error=error)
            if error is not None:
                # connection lost?
                raise error
            # received nothing
            return None, None
        # check data
        error = self._check_received_data(data=data)
        if error is not None:
            # connection lost!
            raise error
        # OK
        return data, remote

    def _sent_to(self, data: bytes, target: tuple) -> int:
        # check socket first
        sock = self.sock
        if sock is None:
            raise socket.error('socket lost, cannot send data: %d byte(s)' % len(data))
        # try to send data
        sent = 0
        try:
            sent = sock.sendto(data, target)
        except socket.error as error:
            error = self._check_socket_error(error=error)
            if error is not None:
                # connection lost?
                raise error
            # buffer overflow!
            if sent == 0:
                return -1
        return sent

    # Override
    def receive(self, max_len: int) -> (Optional[bytes], Optional[tuple]):
        remote = self.remote_address
        if remote is None:
            # not connect (UDP)
            return self._receive_from(max_len=max_len)
        else:
            # connected (TCP/UDP)
            data = self.read(max_len=max_len)
            return data, remote

    # Override
    def send(self, data: bytes, target: tuple) -> int:
        remote = self.remote_address
        if remote is None:
            # not connect (UDP)
            return self._sent_to(data=data, target=target)
        else:
            # connected (TCP/UDP)
            assert target is None or target == remote, 'target address error: %s, %s' % (target, remote)
            # return sock.sendall(data)
            return self.write(data=data)
