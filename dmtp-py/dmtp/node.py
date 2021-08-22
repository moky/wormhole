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

import weakref
from abc import ABC, abstractmethod
from typing import Optional

from udp.ba import ByteArray
from udp.mtp import Header

from .tlv import Field
from .protocol import LocationValue
from .protocol import Command, Message
from .delegate import LocationDelegate


class Node(ABC):

    def __init__(self):
        super().__init__()
        # location delegate
        self.__delegate: Optional[weakref.ReferenceType] = None

    @property
    def delegate(self) -> Optional[LocationDelegate]:
        if self.__delegate is not None:
            return self.__delegate()

    @delegate.setter
    def delegate(self, value: LocationDelegate):
        if value is None:
            self.__delegate = None
        else:
            self.__delegate = weakref.ref(value)

    @abstractmethod
    def _connect(self, remote: tuple):
        raise NotImplemented

    #
    #   Send
    #
    @abstractmethod
    def send_command(self, cmd: Command, destination: tuple) -> bool:
        """
        Send command to destination address

        :param cmd:
        :param destination: remote address
        :return: False on error
        """
        raise NotImplemented

    @abstractmethod
    def send_message(self, msg: Message, destination: tuple) -> bool:
        """
        Send message to destination address

        :param msg:
        :param destination: remote address
        :return: False on error
        """
        raise NotImplemented

    def say_hello(self, destination: tuple) -> bool:
        assert self.delegate is not None, 'contact delegate not set yet'
        mine = self.delegate.current_location()
        if mine is None:
            # raise LookupError('failed to get my location')
            return False
        cmd = Command.hello_command(location=mine)
        return self.send_command(cmd=cmd, destination=destination)

    #
    #   Receive
    #
    def _received(self, head: Header, body: ByteArray, source: tuple):
        data_type = head.data_type
        if data_type.is_message:
            # process after received message data
            fields = Field.parse_fields(data=body)
            msg = Message(data=data_type, fields=fields)
            return self._process_message(msg=msg, source=source)
        elif data_type.is_command:
            # process after received command data
            ok = False
            commands = Command.parse_commands(data=body)
            for cmd in commands:
                if self._process_command(cmd=cmd, source=source):
                    ok = True
            return ok
        else:
            raise TypeError('data type error: %s' % data_type)

    @abstractmethod
    def _process_message(self, msg: Message, source: tuple) -> bool:
        """
        Process received message from remote source address

        :param msg:         message info
        :param source:      remote address
        :return: False on error
        """
        raise NotImplemented

    @abstractmethod
    def _process_command(self, cmd: Command, source: tuple) -> bool:
        """
        Process received command from remote source address

        :param cmd:         command info
        :param source:      remote address
        :return: False on error
        """
        cmd_type = cmd.tag
        cmd_value = cmd.value
        if cmd_type == Command.WHO:
            return self._process_who(source=source)
        elif cmd_type == Command.HELLO:
            assert isinstance(cmd_value, LocationValue), 'login cmd error: %s' % cmd_value
            return self._process_hello(location=cmd_value, source=source)
        elif cmd_type == Command.BYE:
            assert isinstance(cmd_value, LocationValue), 'logout cmd error: %s' % cmd_value
            return self._process_bye(location=cmd_value, source=source)
        else:
            clazz = self.__class__.__name__
            print('%s> unknown command: %s' % (clazz, cmd))
            return False

    #
    #   Process
    #
    def _process_who(self, source: tuple) -> bool:
        # say hi when the sender asked 'Who are you?'
        return self.say_hello(destination=source)

    # noinspection PyUnusedLocal
    def _process_hello(self, location: LocationValue, source: tuple) -> bool:
        # check signature before accept it
        assert self.delegate is not None, 'contact delegate not set yet'
        return self.delegate.store_location(location=location)

    # noinspection PyUnusedLocal
    def _process_bye(self, location: LocationValue, source: tuple) -> bool:
        # check signature before cleaning location
        assert self.delegate is not None, 'contact delegate not set yet'
        return self.delegate.clear_location(location=location)
