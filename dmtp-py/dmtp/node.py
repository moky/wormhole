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
from typing import Optional

from udp import HubListener, Hub
from udp.mtp import PeerDelegate, Peer as UDPPeer
from udp.mtp import Departure, Arrival

from .tlv import Field
from .command import Command, WhoCommand, SignCommand, FromCommand
from .command import Who, Hello, Sign, Call, From, Bye
from .command import CommandValue, LocationValue
from .message import Message
from .contact import Contact


class Peer(UDPPeer, HubListener):

    #
    #   HubListener
    #
    def data_received(self, data: bytes, source: tuple, destination: tuple) -> Optional[bytes]:
        task = Arrival(payload=data, source=source, destination=destination)
        self.pool.append_arrival(task=task)
        return None


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


class Server(Node, ABC):

    def _process_hello(self, location: LocationValue, source: tuple) -> bool:
        mapped_address = location.mapped_address
        if mapped_address is not None and (mapped_address.ip, mapped_address.port) == source:
            if super()._process_hello(location=location, source=source):
                return True
        # response 'SIGN' command with 'ID' and 'ADDR'
        cmd = SignCommand.new(identifier=location.identifier, mapped_address=source)
        self.send_command(cmd=cmd, destination=source)
        return True

    def _process_call(self, receiver: str, source: tuple) -> bool:
        # get locations of receiver
        contact = self.get_contact(identifier=receiver)
        if contact is None:
            addresses = []
        else:
            addresses = contact.addresses
        if len(addresses) == 0:
            # receiver not online
            # respond an empty 'FROM' command to the sender
            cmd = FromCommand.new(identifier=receiver)
            self.send_command(cmd=cmd, destination=source)
            return False
        # receiver is online
        sender = self.get_contact(address=source)
        if sender is None:
            sender_location = None
        else:
            sender_location = sender.get_location(address=source)
        if sender_location is None:
            # ask sender to login again
            cmd = WhoCommand.new()
            self.send_command(cmd=cmd, destination=source)
            return False
        # send command for each address
        for address in addresses:
            receiver_location = contact.get_location(address=address)
            assert receiver_location is not None, 'address error: %s, %s' % (address, receiver)
            # send 'fROM' command with sender's location info to the receiver
            cmd = FromCommand.new(location=sender_location)
            self.send_command(cmd=cmd, destination=address)
            # respond 'FROM' command with receiver's location info to sender
            cmd = FromCommand.new(location=receiver_location)
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
