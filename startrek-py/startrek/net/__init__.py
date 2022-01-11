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


"""
    Architecture
    ~~~~~~~~~~~~

                   Connection        Connection      Connection
                   Delegate          Delegate        Delegate
                       ^                 ^               ^
                       :                 :               :
          ~ ~ ~ ~ ~ ~ ~:~ ~ ~ ~ ~ ~ ~ ~ ~:~ ~ ~ ~ ~ ~ ~ ~:~ ~ ~ ~ ~ ~ ~
                       :                 :               :
            +===+------V-----+====+------V-----+===+-----V------+===+
            ||  | connection |    | connection |   | connection |  ||
            ||  +------------+    +------------+   +------------+  ||
            ||          :                :               :         ||
            ||          :      HUB       :...............:         ||
            ||          :                        :                 ||
            ||     +-----------+           +-----------+           ||
            ||     |  channel  |           |  channel  |           ||
            +======+-----------+===========+-----------+============+
                   |  socket   |           |  socket   |
                   +-----^-----+           +-----^-----+
                         : (TCP)                 : (UDP)
                         :               ........:........
                         :               :               :
          ~ ~ ~ ~ ~ ~ ~ ~:~ ~ ~ ~ ~ ~ ~ ~:~ ~ ~ ~ ~ ~ ~ ~:~ ~ ~ ~ ~ ~ ~
                         :               :               :
                         V               V               V
                    Remote Peer     Remote Peer     Remote Peer
"""

from .hub import Hub
from .channel import Channel
from .connection import Connection
from .delegate import ConnectionDelegate

from .state import ConnectionState, StateMachine as ConnectionStateMachine

from .base_hub import BaseHub
from .base_channel import BaseChannel
from .base_cc import ChannelReader, ChannelWriter
from .base_conn import BaseConnection
from .active_conn import ActiveConnection

__all__ = [

    #
    #   Interfaces
    #
    'Hub',
    'Channel',
    'Connection', 'ConnectionDelegate',

    #
    #   FSM for Connection
    #
    'ConnectionState', 'ConnectionStateMachine',

    #
    #   Base
    #
    'BaseHub',
    'BaseChannel', 'ChannelReader', 'ChannelWriter',
    'BaseConnection', 'ActiveConnection',
]
