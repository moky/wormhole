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
from typing import Optional

from startrek.types import Address
from startrek.net.channel import is_opened
from startrek import BaseChannel, ChannelReader, ChannelWriter


class StreamChannelReader(ChannelReader):

    # Override
    def receive(self, max_len: int) -> (Optional[bytes], Optional[Address]):
        data = self.read(max_len=max_len)
        if data is None or len(data) == 0:
            return None, None
        else:
            return data, self.remote_address


class StreamChannelWriter(ChannelWriter):

    # Override
    def send(self, data: bytes, target: Address) -> int:
        # TCP channel will be always connected
        # so the target address must be the remote address
        remote = self.remote_address
        assert target is None or target == remote, 'target address error: %s, %s' % (target, remote)
        return self.write(data=data)


class StreamChannel(BaseChannel):
    """ Stream Channel """

    def __init__(self, remote: Optional[Address], local: Optional[Address], sock: socket.socket):
        super().__init__(remote=remote, local=local)
        self.__sock = sock
        self._refresh_flags(sock=sock)

    # Override
    def _get_socket(self) -> Optional[socket.socket]:
        return self.__sock

    # Override
    def _set_socket(self, sock: Optional[socket.socket]):
        # 1. check old socket
        old = self._get_socket()
        if old is not None and old is not sock:
            if is_opened(sock=old):
                close_socket(sock=old)
        # 2. set new socket
        self.__sock = sock

    # Override
    def _create_reader(self):
        return StreamChannelReader(channel=self)

    # Override
    def _create_writer(self):
        return StreamChannelWriter(channel=self)


def close_socket(sock: socket.socket):
    try:
        # sock.shutdown(socket.SHUT_RDWR)
        sock.close()
    except socket.error:
        pass
