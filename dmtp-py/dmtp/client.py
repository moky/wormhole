# -*- coding: utf-8 -*-
#
#   DMTP: Direct Message Transfer Protocol
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

from abc import ABC

from .command import Command
from .command import Sign, From
from .command import LocationValue
from .node import Node


class Client(Node, ABC):

    # noinspection PyUnusedLocal
    def _process_sign(self, location: LocationValue, destination: tuple) -> bool:
        # sign your location for login
        assert self.delegate is not None, 'contact delegate not set'
        mine = self.delegate.sign_location(location=location)
        if mine is None:
            raise LookupError('failed to sign the location: %s' % location)
            # return False
        # update the signed location
        if self.delegate.update_location(location=mine):
            # say hi with new location
            return self.say_hi(destination=destination)

    def _process_from(self, location: LocationValue) -> bool:
        # when someone is calling you
        # respond anything (say 'HI') to build the connection.
        assert self.delegate is not None, 'contact delegate not set'
        if self.delegate.update_location(location=location):
            if location.source_address is not None:
                address = (location.source_address.ip, location.source_address.port)
                self.peer.connect(remote_address=address)
                self.say_hi(destination=address)
            if location.mapped_address is not None:
                address = (location.mapped_address.ip, location.mapped_address.port)
                self.peer.connect(remote_address=address)
                self.say_hi(destination=address)
            return True

    def process_command(self, cmd: Command, source: tuple) -> bool:
        cmd_type = cmd.tag
        cmd_value = cmd.value
        if cmd_type == Sign:
            assert isinstance(cmd_value, LocationValue), 'sign cmd error: %s' % cmd_value
            return self._process_sign(location=cmd_value, destination=source)
        elif cmd_type == From:
            assert isinstance(cmd_value, LocationValue), 'call from error: %s' % cmd_value
            return self._process_from(location=cmd_value)
        else:
            return super().process_command(cmd=cmd, source=source)
