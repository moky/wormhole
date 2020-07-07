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
from abc import abstractmethod
from typing import Optional

from udp.tlv import Data
from udp.mtp import Package, Command as DataTypeCommand, Message as DataTypeMessage
from udp.mtp import PeerHandler, Pool
from udp.mtp import Departure

from .tlv import Field
from .values import LocationValue
from .command import Command, HelloCommand
from .message import Message
from .peer import Hub, Peer, LocationDelegate


class Node(PeerHandler):

    def __init__(self, peer: Peer=None, local_address: tuple=None, hub: Hub=None, pool: Pool=None):
        super().__init__()
        if peer is None:
            peer = self.__create_peer(local_address=local_address, hub=hub, pool=pool)
        self.__peer = peer
        peer.handler = self
        # location delegate
        self.__delegate: weakref.ReferenceType = None

    # noinspection PyMethodMayBeStatic
    def __create_peer(self, local_address: tuple, hub: Hub=None, pool: Pool=None):
        peer = Peer(local_address=local_address, hub=hub, pool=pool)
        # peer.start()
        return peer

    @property
    def peer(self) -> Peer:
        return self.__peer

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

    def start(self):
        # start peer
        self.peer.start()

    def stop(self):
        # stop peer
        self.peer.stop()

    #
    #   Send
    #
    def send_command(self, cmd: Command, destination: tuple) -> Departure:
        """
        Send command to destination address

        :param cmd:
        :param destination: remote address
        :return: departure task with 'trans_id' in the payload
        """
        pack = Package.new(data_type=DataTypeCommand, body=cmd)
        return self.peer.send_command(pack=pack, destination=destination)

    def send_message(self, msg: Message, destination: tuple) -> Departure:
        """
        Send message to destination address

        :param msg:
        :param destination: remote address
        :return: departure task with 'trans_id' in the payload
        """
        pack = Package.new(data_type=DataTypeMessage, body=msg)
        return self.peer.send_message(pack=pack, destination=destination)

    #
    #   Process
    #

    def say_hello(self, destination: tuple) -> bool:
        assert self.delegate is not None, 'contact delegate not set yet'
        mine = self.delegate.current_location()
        if mine is None:
            # raise LookupError('failed to get my location')
            return False
        cmd = HelloCommand.new(location=mine)
        self.send_command(cmd=cmd, destination=destination)
        return True

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

    @abstractmethod
    def process_command(self, cmd: Command, source: tuple) -> bool:
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

    @abstractmethod
    def process_message(self, msg: Message, source: tuple) -> bool:
        """
        Process received message from remote source address

        :param msg:         message info
        :param source:      remote address
        :return: False on error
        """
        pass

    #
    #   PeerHandler
    #
    def received_command(self, cmd: Data, source: tuple, destination: tuple) -> bool:
        commands = Command.parse_all(data=cmd)
        for pack in commands:
            assert isinstance(pack, Command), 'command error: %s' % pack
            self.process_command(cmd=pack, source=source)
        return True

    def received_message(self, msg: Data, source: tuple, destination: tuple) -> bool:
        fields = Field.parse_all(data=msg)
        assert len(fields) > 0, 'message error: %s' % msg
        pack = Message(fields=fields, data=msg)
        return self.process_message(msg=pack, source=source)
