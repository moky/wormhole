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
import socket
import traceback
from typing import Optional, Tuple

from startrek import SocketAddress
from startrek import SocketHelper


# noinspection PyMethodMayBeStatic
class DatagramHelper(SocketHelper):

    #
    #   Async
    #

    # Override
    async def disconnect(self, sock: socket.socket) -> bool:
        """ Close socket """
        if self.is_closed(sock=sock):
            return True
        # check for master socket
        remote = self.get_remote_address(sock=sock)
        if remote is None:
            # cannot close master socket
            return True
        try:
            # TODO: async api?
            sock.close()
            # return not self.is_connected(sock=sock)
            return True
        # except (OSError, socket.error):
        #     return False
        except Exception as error:
            print('[Socket] cannot close socket: %s, %s' % (sock, error))
            traceback.print_exc()
            return False

    async def send_to(self, sock: socket.socket, data: bytes, target: SocketAddress) -> int:
        """ Send datagram package """
        # return sock.sendto(data, target)
        loop = asyncio.get_event_loop()
        try:
            # return await loop.sock_sendto(sock, data, target)
            return await loop.run_in_executor(
                None,
                sock.sendto,
                data,
                target,
            )
        except BlockingIOError:
            await asyncio.sleep(0.01)
            raise
        except OSError:
            raise
        except Exception as error:
            raise OSError('Failed to send datagram: %s' % error)

    async def receive_from(self, sock: socket.socket, max_len: int) -> Tuple[Optional[bytes], Optional[SocketAddress]]:
        """ Receive datagram package """
        # return sock.recvfrom(max_len)
        loop = asyncio.get_event_loop()
        try:
            # return await loop.sock_recvfrom(sock, max_len)
            return await loop.run_in_executor(
                None,
                sock.recvfrom,
                max_len,
            )
        except BlockingIOError:
            await asyncio.sleep(0.01)
            raise
        except OSError:
            raise
        except Exception as error:
            raise OSError('Failed to receive datagram: %s' % error)
