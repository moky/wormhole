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

from abc import ABC, abstractmethod

from udp import Peer, PeerDelegate, Departure

from .command import *
from .message import *


class Contact:

    def __init__(self, identifier: str):
        super().__init__()
        self.__id = identifier
        self.__location: LocationValue = None
        self.__address: tuple = None

    @property
    def identifier(self) -> str:
        return self.__id

    @property
    def location(self) -> Optional[LocationValue]:
        """ Source Address, Mapped Address, Relayed Address """
        return self.__location

    def check_location(self, location: LocationValue) -> bool:
        if location.identifier != self.identifier:
            # assert False, 'location ID not match: %s, %s' % (self.identifier, location)
            return False
        if self.__location is not None and self.__location.timestamp > location.timestamp:
            # expired location
            return False
        # TODO: check signature
        return True

    def update_location(self, location: LocationValue) -> bool:
        if self.check_location(location=location):
            self.__location = location
            return True

    def remove_location(self, location: LocationValue):
        if self.check_location(location=location):
            self.__location = None
            return True

    @property
    def address(self) -> tuple:
        """ Connected Address """
        return self.__address

    def update_address(self, address: tuple) -> bool:
        assert self.location is not None, 'location should not empty'
        # 1st, check source address
        source_address = self.location.source_address
        if source_address is not None:
            if (source_address.ip, source_address.port) == self.__address:
                # connected to source address
                return self.__address == address
            if (source_address.ip, source_address.port) == address:
                self.__address = address
                return True
        # 2nd, check mapped address
        mapped_address = self.location.mapped_address
        if mapped_address is not None:
            if (mapped_address.ip, mapped_address.port) == self.__address:
                # connected to mapped address
                return self.__address == address
            if (mapped_address.ip, mapped_address.port) == address:
                self.__address = address
                return True
        # 3rd, check relayed address
        relayed_address = self.location.relayed_address
        if relayed_address is not None:
            if (relayed_address.ip, relayed_address.port) == self.__address:
                # connected to relayed address
                return self.__address == address
            if (relayed_address.ip, relayed_address.port) == address:
                self.__address = address
                return True
        assert False, 'failed to update address: %s -> %s' % (address, self.identifier)


class Node(PeerDelegate):

    def __init__(self):
        super().__init__()
        self.__peer: Peer = None
        # user ID
        self.identifier: str = None
        # online contacts
        self.__contacts: dict = {}  # ID -> Contact
        self.__map: dict = {}       # (IP, port) -> Contact

    #
    #   Peer (send/receive data)
    #
    @property
    def peer(self) -> Peer:
        if self.__peer is None:
            self.__peer = self._create_peer()
        return self.__peer

    def _create_peer(self) -> Peer:
        peer = Peer()
        peer.delegate = self
        peer.start()
        return peer

    #
    #   Contacts (with location info)
    #
    @property
    def contacts(self) -> dict:
        return self.__contacts

    # noinspection PyMethodMayBeStatic
    def _create_contact(self, identifier: str) -> Contact:
        return Contact(identifier=identifier)

    def set_location(self, location: LocationValue) -> bool:
        identifier = location.identifier
        if identifier is None:
            return False
        contact = self.__contacts.get(identifier)
        if contact is None:
            contact = self._create_contact(identifier=identifier)
        if contact.update_location(location=location):
            self.__contacts[identifier] = contact
            return True

    def get_location(self, identifier: str=None, address: tuple=None) -> Optional[LocationValue]:
        if identifier is None:
            assert len(address) == 2, 'address error: %s' % str(address)
            contact = self.__map.get(address)
        else:
            contact = self.__contacts.get(identifier)
        if contact is not None:
            return contact.location

    def remove_location(self, location: LocationValue) -> bool:
        """ Logout """
        identifier = location.identifier
        contact = self.__contacts.get(identifier)
        if contact is None:
            return False
        assert isinstance(contact, Contact), 'contact error: %s' % contact
        if contact.remove_location(location=location):
            self.__contacts.pop(identifier, None)
            if location.source_address is not None:
                address = location.source_address
                address = (address.ip, address.port)
                self.__map.pop(address, None)
            if location.mapped_address is not None:
                address = location.mapped_address
                address = (address.ip, address.port)
                self.__map.pop(address, None)
            return True

    def update_address(self, address: tuple, contact: Contact) -> bool:
        if contact.update_address(address=address):
            self.__map[address] = contact
            return True

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
        return self.peer.send_command(pack=cmd.data, destination=destination)

    def send_message(self, msg: Message, destination: tuple) -> Departure:
        """
        Send message to destination address

        :param msg:
        :param destination: remote address
        :return: departure task with 'trans_id' in the payload
        """
        return self.peer.send_message(pack=msg.data, destination=destination)

    #
    #   Process
    #
    def say_hi(self, destination: tuple) -> bool:
        """
        Send 'HI' command to tell the server who you are

        :param destination: server address
        :return: False on failed
        """
        location = self.get_location(identifier=self.identifier)
        if location is None:
            cmd = HelloCommand.new(identifier=self.identifier)
        else:
            cmd = HelloCommand.new(location=location)
        self.send_command(cmd=cmd, destination=destination)
        return True

    def _process_who(self, source: tuple) -> bool:
        # say hi when the sender asked 'Who are you?'
        return self.say_hi(destination=source)

    # noinspection PyUnusedLocal
    def _process_login(self, location: LocationValue, source: tuple) -> bool:
        # check signature before accept it
        return self.set_location(location=location)

    # noinspection PyUnusedLocal
    def _process_logout(self, location: LocationValue, source: tuple) -> bool:
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
        cmd_type = cmd.type
        cmd_value = cmd.value
        if cmd_type == Who:
            return self._process_who(source=source)
        elif cmd_type == Hello:
            assert isinstance(cmd_value, LocationValue), 'login cmd error: %s' % cmd_value
            return self._process_login(location=cmd_value, source=source)
        elif cmd_type == Bye:
            assert isinstance(cmd_value, LocationValue), 'logout cmd error: %s' % cmd_value
            return self._process_logout(location=cmd_value, source=source)
        else:
            clazz = self.__class__.__name__
            print('%s> unknown command: %s' % (clazz, cmd))

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


class Server(Node, ABC):

    def _process_login(self, location: LocationValue, source: tuple) -> bool:
        mapped_address = location.mapped_address
        if mapped_address is not None and (mapped_address.ip, mapped_address.port) == source:
            if super()._process_login(location=location, source=source):
                return True
        # response 'SIGN' command with 'ID' and 'ADDR'
        cmd = SignCommand.new(identifier=location.identifier, mapped_address=source)
        self.send_command(cmd=cmd, destination=source)
        return True

    def __process_call(self, value: CommandValue, source: tuple) -> bool:
        receiver = self.get_location(identifier=value.identifier)
        if receiver is None or receiver.mapped_address is None:
            # receiver not online
            # respond an empty 'FROM' command to the sender
            cmd = FromCommand.new(identifier=value.identifier)
            self.send_command(cmd=cmd, destination=source)
        else:
            # receiver is online
            sender = self.get_location(address=source)
            if sender is None:
                # ask sender to login again
                cmd = WhoCommand.new()
                self.send_command(cmd=cmd, destination=source)
            else:
                # send 'fROM' command with sender's location info to the receiver
                cmd = FromCommand.new(location=sender)
                address = receiver.mapped_address
                self.send_command(cmd=cmd, destination=(address.ip, address.port))
                # respond 'FROM' command with receiver's location info to sender
                cmd = FromCommand.new(location=receiver)
                self.send_command(cmd=cmd, destination=source)
        return True

    def process_command(self, cmd: Command, source: tuple) -> bool:
        cmd_type = cmd.type
        cmd_value = cmd.value
        if cmd_type == Call:
            assert isinstance(cmd_value, CommandValue), 'call cmd error: %s' % cmd_value
            return self.__process_call(value=cmd_value, source=source)
        else:
            return super().process_command(cmd=cmd, source=source)


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

    def connect(self, location: LocationValue=None, remote_address: tuple=None) -> bool:
        """
        Send something to punch a tunnel for that location

        :param location:       LocationValue contains ID, IP, port
        :param remote_address: server or remote user's address
        :return:
        """
        if location is None:
            assert len(remote_address) == 2, 'remote address error: %s' % str(remote_address)
            return self.say_hi(destination=remote_address)
        elif self.set_location(location=location):
            ok1 = False
            ok2 = False
            if location.source_address is not None:
                address = (location.source_address.ip, location.source_address.port)
                ok1 = self.say_hi(destination=address)
            if location.mapped_address is not None:
                address = (location.mapped_address.ip, location.mapped_address.port)
                ok2 = self.say_hi(destination=address)
            return ok1 or ok2

    def process_command(self, cmd: Command, source: tuple) -> bool:
        cmd_type = cmd.type
        cmd_value = cmd.value
        if cmd_type == Sign:
            assert isinstance(cmd_value, LocationValue), 'sign cmd error: %s' % cmd_value
            # sign your location for login
            return self.sign_in(location=cmd_value, destination=source)
        elif cmd_type == From:
            assert isinstance(cmd_value, LocationValue), 'call from error: %s' % cmd_value
            # when someone is calling you
            # respond anything (say 'HI') to build the connection.
            return self.connect(location=cmd_value, remote_address=source)
        else:
            return super().process_command(cmd=cmd, source=source)
