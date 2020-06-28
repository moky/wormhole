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

from .command import Command, WhoCommand, SignCommand, FromCommand
from .command import Call
from .command import CommandValue, LocationValue

from .contact import Session
from .node import Node


class Server(Node, ABC):

    def _process_hello(self, location: LocationValue, source: tuple) -> bool:
        address = location.mapped_address
        if address is not None \
                and address.port == source[1] and address.ip == source[0]:
            # check 'MAPPED-ADDRESS'
            if super()._process_hello(location=location, source=source):
                # location info accepted
                return True
        # response 'SIGN' command with 'ID' and 'ADDR'
        cmd = SignCommand.new(identifier=location.identifier, mapped_address=source)
        self.send_command(cmd=cmd, destination=source)
        return True

    def _process_call(self, receiver: str, source: tuple) -> bool:
        assert self.delegate is not None, 'contact delegate not set yet'
        if receiver is None:
            # raise ValueError('receiver ID not found')
            return False
        # get sessions of receiver
        sessions = self.get_sessions(identifier=receiver)
        if len(sessions) == 0:
            # receiver offline
            # respond an empty 'FROM' command to the sender
            cmd = FromCommand.new(identifier=receiver)
            self.send_command(cmd=cmd, destination=source)
            return False
        # receiver online
        sender_location = self.delegate.get_location(address=source)
        if sender_location is None:
            # sender offline, ask sender to login again
            cmd = WhoCommand.new()
            self.send_command(cmd=cmd, destination=source)
            return False
        # sender online
        # send command for each address
        for item in sessions:
            assert isinstance(item, Session), 'session info error: %s' % item
            # send 'fROM' command with sender's location info to the receiver
            cmd = FromCommand.new(location=sender_location)
            self.send_command(cmd=cmd, destination=item.address)
            # respond 'FROM' command with receiver's location info to sender
            cmd = FromCommand.new(location=item.location)
            self.send_command(cmd=cmd, destination=source)
        return True

    def process_command(self, cmd: Command, source: tuple) -> bool:
        cmd_type = cmd.tag
        cmd_value = cmd.value
        if cmd_type == Call:
            assert isinstance(cmd_value, CommandValue), 'call cmd error: %s' % cmd_value
            return self._process_call(receiver=cmd_value.identifier, source=source)
        else:
            return super().process_command(cmd=cmd, source=source)
