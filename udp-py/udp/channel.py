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

from startrek.net.base_channel import sendall
from startrek import BaseChannel


class PackageChannel(BaseChannel):
    """ Discrete Package Channel """

    # Override
    def receive(self, max_len: int) -> (bytes, tuple):
        sock = self.sock
        if sock is None:
            raise socket.error('socket lost, cannot read data')
        remote = self.remote_address
        # try to receive data
        try:
            if remote is None:
                # UDP receiving
                data, remote = sock.recvfrom(max_len)
            else:
                # connected (TCP/UDP)
                data = sock.recv(max_len)
        except socket.error as error:
            # the socket will raise 'Resource temporarily unavailable'
            # when received nothing in non-blocking mode,
            # here we should ignore this exception.
            if not self.blocking:
                if error.strerror == 'Resource temporarily unavailable':
                    # received nothing
                    return None, None
            raise error
        # check data
        if data is None or len(data) == 0:
            # in blocking mode, the socket will wait until received something,
            # but if timeout was set, it will return None too, it's normal;
            # otherwise, we know the connection was lost.
            if sock.gettimeout() is None:  # and self.blocking:
                raise socket.error('remote peer reset socket')
        return data, remote

    # Override
    def send(self, data: bytes, target: tuple) -> int:
        sock = self.sock
        if sock is None:
            raise socket.error('socket lost, cannot send data: %d byte(s)' % len(data))
        remote = self.remote_address
        if remote is None:
            # UDP sending
            return sock.sendto(data, target)
        else:
            # connected (TCP/UDP)
            assert target is None or target == remote,\
                'the target must equal to remote address: %s, %s' % (target, remote)
            # return sock.sendall(data)
            return sendall(data=data, sock=sock)
