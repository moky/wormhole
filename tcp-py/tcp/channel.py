# -*- coding: utf-8 -*-
#
#   TCP: Transmission Control Protocol
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
import time
from typing import Optional, Tuple

from startrek.types import SocketAddress
from startrek import BaseChannel, ChannelReader, ChannelWriter


class StreamChannelReader(ChannelReader):

    # Override
    def receive(self, max_len: int) -> Tuple[Optional[bytes], Optional[SocketAddress]]:
        data = self.read(max_len=max_len)
        if data is None or len(data) == 0:
            return None, None
        else:
            return data, self.remote_address


class StreamChannelWriter(ChannelWriter):

    # Override
    def send(self, data: bytes, target: SocketAddress) -> int:
        # TCP channel will be always connected
        # so the target address must be the remote address
        remote = self.remote_address
        assert target is None or target == remote, 'target error: %s, remote=%s' % (target, remote)
        return self.write(data=data)


class StreamChannel(BaseChannel):
    """ Stream Channel """

    # Override
    def _create_reader(self):
        return StreamChannelReader(channel=self)

    # Override
    def _create_writer(self):
        return StreamChannelWriter(channel=self)


def create_socket(remote: SocketAddress, local: Optional[SocketAddress]) -> Optional[socket.socket]:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 0)
        sock.setblocking(True)
        # try to bind
        if local is not None:
            sock.bind(local)
        # try to connect
        sock.connect(remote)
        sock.setblocking(False)
        return sock
    except socket.error as error:
        print('[%s] [TCP] failed to create socket %s -> %s: %s' % (current_time(), local, remote, error))


def current_time() -> str:
    now = time.time()
    localtime = time.localtime(now)
    return time.strftime('%Y-%m-%d %H:%M:%S', localtime)
