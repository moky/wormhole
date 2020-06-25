# -*- coding: utf-8 -*-
#
#   DMTP: Direct Message Transfer Protocol
#
#                                Written in 2020 by Moky <albert.moky@gmail.com>
#
# ==============================================================================
# MIT License
#
# Copyright (c) 2019 Albert Moky
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

from abc import abstractmethod

from .command import Command
from .command import Sign, From
from .command import LocationValue
from .node import Node


class Client(Node):

    @abstractmethod
    def sign_in(self, location: LocationValue, destination: tuple) -> bool:
        """
        Sign the addresses and time in the location value with private key

        :param location:    LocationValue contains ID, IP, port
        :param destination: server's address
        :return: False on error
        """
        pass

    def connect(self, remote_address: tuple) -> bool:
        """
        Send something to punch a tunnel for that location

        :param remote_address: server or remote user's address
        :return:
        """
        conn = self.hub.connect(destination=remote_address, source=self.local_address)
        if conn is None:
            return False
        return self.say_hi(destination=remote_address)

    def _process_sign(self, location: LocationValue, destination: tuple) -> bool:
        # sign your location for login
        return self.sign_in(location=location, destination=destination)

    def _process_from(self, location: LocationValue) -> bool:
        # when someone is calling you
        # respond anything (say 'HI') to build the connection.
        if self.set_location(location=location):
            ok1 = False
            ok2 = False
            if location.source_address is not None:
                address = (location.source_address.ip, location.source_address.port)
                ok1 = self.connect(remote_address=address)
            if location.mapped_address is not None:
                address = (location.mapped_address.ip, location.mapped_address.port)
                ok2 = self.connect(remote_address=address)
            return ok1 or ok2

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
