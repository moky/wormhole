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

from typing import Optional, Union


# Addresses can be either tuples of varying lengths (AF_INET, AF_INET6,
# AF_NETLINK, AF_TIPC) or strings (AF_UNIX).
Address = Union[tuple, str]
# TODO: Most methods allow bytes as address objects


class AddressPairObject:

    def __init__(self, remote: Optional[Address], local: Optional[Address]):
        super().__init__()
        self._remote = remote
        self._local = local

    @property
    def remote_address(self) -> Optional[Address]:
        return self._remote

    @property
    def local_address(self) -> Optional[Address]:
        return self._local

    def __str__(self) -> str:
        cname = self.__class__.__name__
        return '<%s: remote=%s, local=%s />' % (cname, self.remote_address, self.local_address)

    def __repr__(self) -> str:
        cname = self.__class__.__name__
        return '<%s: remote=%s, local=%s />' % (cname, self.remote_address, self.local_address)

    def __hash__(self):
        # same algorithm as Pair::hashCode()
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # remote's hashCode is multiplied by an arbitrary prime number (13)
        # in order to make sure there is a difference in the hashCode between
        # these two parameters:
        #     remote: a  local: aa
        #     local: aa  remote: a
        remote = self._remote
        local = self._local
        if remote is None:
            return hash(local)
        elif local is None:
            return hash(remote) * 13
        else:
            return hash(remote) * 13 + hash(local)

    def __eq__(self, other):
        if other is None:
            return self._remote is None and self._local is None
        elif other is self:
            return True
        elif isinstance(other, AddressPairObject):
            return self._remote == other._remote and self._local == other._local

    def __ne__(self, other):
        if other is None:
            return self._remote is not None or self._local is not None
        elif other is self:
            return False
        elif isinstance(other, AddressPairObject):
            return self._remote != other._remote or self._local != other._local
        else:
            return True
