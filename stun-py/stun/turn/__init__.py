# -*- coding: utf-8 -*-
#
#   TURN: Traversal Using Relays around NAT
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

"""
Mahy, et al.                 Standards Track                    [Page 5]

RFC 5766                          TURN                        April 2010


                                        Peer A
                                        Server-Reflexive    +---------+
                                        Transport Address   |         |
                                        192.0.2.150:32102   |         |
                                            |              /|         |
                          TURN              |            / ^|  Peer A |
    Client's              Server            |           /  ||         |
    Host Transport        Transport         |         //   ||         |
    Address               Address           |       //     |+---------+
   10.1.1.2:49721       192.0.2.15:3478     |+-+  //     Peer A
            |               |               ||N| /       Host Transport
            |   +-+         |               ||A|/        Address
            |   | |         |               v|T|     192.168.100.2:49582
            |   | |         |               /+-+
 +---------+|   | |         |+---------+   /              +---------+
 |         ||   |N|         ||         | //               |         |
 | TURN    |v   | |         v| TURN    |/                 |         |
 | Client  |----|A|----------| Server  |------------------|  Peer B |
 |         |    | |^         |         |^                ^|         |
 |         |    |T||         |         ||                ||         |
 +---------+    | ||         +---------+|                |+---------+
                | ||                    |                |
                | ||                    |                |
                +-+|                    |                |
                   |                    |                |
                   |                    |                |
             Client's                   |            Peer B
             Server-Reflexive    Relayed             Transport
             Transport Address   Transport Address   Address
             192.0.2.1:7000      192.0.2.15:50000     192.0.2.210:49191
"""

from .values import *

name = "TURN"

__author__ = 'Albert Moky'

__all__ = [

    #
    #  Attributes
    #

    'ChannelNumber', 'Lifetime',
    # 'BandWidth',
    'XorPeerAddress', 'Data', 'XorRelayedAddress',
    'EvenPort', 'RequestedTransport', 'DontFragment',
    # 'TimerVal',
    'ReservationToken',

    'XorPeerAddressValue', 'XorRelayedAddressValue',
]
