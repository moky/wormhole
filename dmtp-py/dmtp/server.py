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

from .protocol import Command
from .protocol import CommandValue, LocationValue

from .node import Node


class Server(Node, ABC):

    def _process_hello(self, location: LocationValue, source: tuple) -> bool:
        # check 'MAPPED-ADDRESS'
        if location.mapped_address == source:
            if super()._process_hello(location=location, source=source):
                # location info accepted, create a connection to this source
                self._connect(remote=source)
                return True
        # response 'SIGN' command with 'ID' and 'ADDR'
        cmd = Command.sign_command(identifier=location.identifier, mapped_address=source)
        return self.send_command(cmd=cmd, destination=source)

    def _process_call(self, receiver: str, source: tuple) -> bool:
        delegate = self.delegate
        assert delegate is not None, 'contact delegate not set yet'
        if receiver is None:
            # raise ValueError('receiver ID not found')
            return False
        # get sessions of receiver
        locations = delegate.get_locations(identifier=receiver)
        if len(locations) == 0:
            # receiver offline
            # respond an empty 'FROM' command to the sender
            cmd = Command.from_command(identifier=receiver)
            self.send_command(cmd=cmd, destination=source)
            return False
        # receiver online
        sender_location = delegate.get_location(address=source)
        if sender_location is None:
            # sender offline, ask sender to login again
            cmd = Command.who_command()
            self.send_command(cmd=cmd, destination=source)
            return False
        # sender online
        # send command for each address
        for loc in locations:
            assert isinstance(loc, LocationValue), 'location info error: %s' % loc
            address = loc.mapped_address
            if address is None:
                continue
            # send 'FROM' command with sender's location info to the receiver
            cmd = Command.from_command(location=sender_location)
            self.send_command(cmd=cmd, destination=address)
            # respond 'FROM' command with receiver's location info to sender
            cmd = Command.from_command(location=loc)
            self.send_command(cmd=cmd, destination=source)
        return True

    def _process_command(self, cmd: Command, source: tuple) -> bool:
        cmd_type = cmd.tag
        cmd_value = cmd.value
        if cmd_type == Command.CALL:
            assert isinstance(cmd_value, CommandValue), 'call cmd error: %s' % cmd_value
            return self._process_call(receiver=cmd_value.identifier, source=source)
        else:
            return super()._process_command(cmd=cmd, source=source)
