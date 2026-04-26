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

import select
import socket
from typing import Optional

from ..types import SocketAddress


def get_local_address(sock: socket.socket) -> Optional[SocketAddress]:
    try:
        return sock.getsockname()
    except (OSError, socket.error):
        return None
    except Exception as error:
        print('[NET] unexpected error getting local address: %s' % error)
        return None


def get_remote_address(sock: socket.socket) -> Optional[SocketAddress]:
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


def is_blocking(sock: socket.socket) -> bool:
    try:
        return sock.getblocking()
    except (OSError, socket.error):
        return False
    except Exception as error:
        print('[NET] unexpected error getting blocking: %s' % error)
        return False


def is_bound(sock: socket.socket) -> bool:
    return get_local_address(sock=sock) is not None


def is_connected(sock: socket.socket) -> bool:
    return get_remote_address(sock=sock) is not None


def is_closed(sock: socket.socket) -> bool:
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


def is_available(sock: socket.socket) -> bool:
    """ Ready for reading """
    try:
        ready, _, _ = select.select([sock], [], [], 0)
        return sock in ready
    except (OSError, ValueError):
        return False
    except Exception as error:
        print('[NET] unexpected error checking available: %s' % error)
        return False


def is_vacant(sock: socket.socket) -> bool:
    """ Ready for writing """
    try:
        _, ready, _ = select.select([], [sock], [], 0)
        return sock in ready
    except (OSError, ValueError):
        return False
    except Exception as error:
        print('[NET] unexpected error checking vacant: %s' % error)
        return False
