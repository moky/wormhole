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
from typing import Optional

from udp import Hub
from udp.mtp import PeerDelegate
from udp.mtp import Departure

from .tlv import Field
from .command import Command, Who, Hello, Bye
from .command import LocationValue
from .message import Message
from .contact import Contact
from .peer import Peer


class Node(PeerDelegate):

    def __init__(self, host: str, port: int):
        super().__init__()
        self.__local_address = (host, port)
        self.__peer: Peer = None
        self.__hub: Hub = None

    @property
    def local_address(self) -> tuple:
        return self.__local_address

    @property
    def peer(self) -> Peer:
        if self.__peer is None:
            self.__peer = self._create_peer()
        return self.__peer

    def _create_peer(self) -> Peer:
        peer = Peer()
        peer.delegate = self
        # peer.start()
        return peer

    @property
    def hub(self) -> Hub:
        if self.__hub is None:
            self.__hub = self._create_hub()
        return self.__hub

    def _create_hub(self) -> Hub:
        assert isinstance(self.__local_address, tuple), 'local address error'
        host = self.__local_address[0]
        port = self.__local_address[1]
        assert port > 0, 'invalid port: %d' % port
        hub = Hub()
        hub.open(host=host, port=port)
        hub.add_listener(self.peer)
        # hub.start()
        return hub

    def start(self):
        # start peer
        if not self.peer.running:
            self.peer.start()
        # start hub
        if not self.hub.running:
            self.hub.start()

    def stop(self):
        # stop hub
        if self.__hub is not None:
            self.__hub.stop()
        # stop peer
        if self.__peer is not None:
            self.__peer.stop()

    #
    #   Contacts (with locations)
    #

    # noinspection PyMethodMayBeStatic
    def _create_contact(self, identifier: str) -> Contact:
        return Contact(identifier=identifier)

    @abstractmethod
    def get_contact(self, identifier: str=None, address: tuple=None) -> Optional[Contact]:
        """ get contact by ID or address """
        raise NotImplemented

    @abstractmethod
    def set_location(self, location: LocationValue) -> bool:
        """ Login """
        raise NotImplemented

    @abstractmethod
    def remove_location(self, location: LocationValue) -> bool:
        """ Logout """
        raise NotImplemented

    @abstractmethod
    def update_address(self, address: tuple, contact: Contact) -> bool:
        """ Switch IP and port """
        raise NotImplemented

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
        return self.peer.send_command(pack=cmd.data, destination=destination, source=self.local_address)

    def send_message(self, msg: Message, destination: tuple) -> Departure:
        """
        Send message to destination address

        :param msg:
        :param destination: remote address
        :return: departure task with 'trans_id' in the payload
        """
        return self.peer.send_message(pack=msg.data, destination=destination, source=self.local_address)

    #
    #   Process
    #
    @abstractmethod
    def say_hi(self, destination: tuple) -> bool:
        """
        Send 'HI' command to tell the server who you are

        :param destination: server address
        :return: False on failed
        """
        pass

    def _process_who(self, source: tuple) -> bool:
        # say hi when the sender asked 'Who are you?'
        return self.say_hi(destination=source)

    # noinspection PyUnusedLocal
    def _process_hello(self, location: LocationValue, source: tuple) -> bool:
        # check signature before accept it
        if self.set_location(location=location):
            contact = self.get_contact(identifier=location.identifier)
            assert isinstance(contact, Contact), 'contact error: %s -> %s' % (location.identifier, contact)
            return self.update_address(address=source, contact=contact)

    # noinspection PyUnusedLocal
    def _process_bye(self, location: LocationValue, source: tuple) -> bool:
        # check signature before cleaning location
        return self.remove_location(location=location)

    #
    #   Receive
    #
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
        if cmd_type == Who:
            return self._process_who(source=source)
        elif cmd_type == Hello:
            assert isinstance(cmd_value, LocationValue), 'login cmd error: %s' % cmd_value
            return self._process_hello(location=cmd_value, source=source)
        elif cmd_type == Bye:
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
    #   PeerDelegate
    #
    def send_data(self, data: bytes, destination: tuple, source: tuple) -> int:
        return self.hub.send(data=data, destination=destination, source=source)

    def received_command(self, cmd: bytes, source: tuple, destination: tuple) -> bool:
        commands = Command.parse_all(data=cmd)
        for pack in commands:
            assert isinstance(pack, Command), 'command error: %s' % pack
            self.process_command(cmd=pack, source=source)
        return True

    def received_message(self, msg: bytes, source: tuple, destination: tuple) -> bool:
        fields = Field.parse_all(data=msg)
        assert len(fields) > 0, 'message error: %s' % msg
        pack = Message(fields=fields, data=msg)
        return self.process_message(msg=pack, source=source)
