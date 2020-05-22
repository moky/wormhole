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
from typing import Union

from udp import Peer, PeerDelegate, Hub

from .command import *
from .message import *


class Node(PeerDelegate):

    def __init__(self, hub: Hub):
        super().__init__()
        # create inner peer
        peer = Peer()
        peer.delegate = self
        peer.start()
        hub.add_listener(peer)
        self.__peer = peer
        self.__hub = hub

    @abstractmethod
    def set_location(self, value: LocationValue) -> bool:
        """
        Check signature for MAPPED-ADDRESS before accept it

        :param value:
        :return: False on error
        """
        pass

    @abstractmethod
    def get_location(self, uid: str=None, source: tuple=None) -> Optional[LocationValue]:
        """
        Get online info by user ID or (ip, port)

        :param uid:    user ID
        :param source: public IP and port
        :return: LocationValue when user's online now
        """
        pass

    def send_command(self, cmd: Command, destination: tuple):
        """
        Send command to destination address

        :param cmd:
        :param destination: remote address
        :return:
        """
        self.__peer.send_command(data=cmd.data, destination=destination)

    def send_message(self, msg: Message, destination: tuple):
        """
        Send message to destination address

        :param msg:
        :param destination: remote address
        :return:
        """
        self.__peer.send_message(data=msg.data, destination=destination)

    @abstractmethod
    def process_command(self, cmd: Command, source: tuple) -> bool:
        """
        Process received command from remote source address

        :param cmd:         command info
        :param source:      remote address
        :return: False on error
        """
        pass

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
    def send_data(self, data: bytes, destination: tuple, source: Union[tuple, int] = None) -> int:
        return self.__hub.send(data=data, destination=destination, source=source)

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

    def __process_login(self, value: LocationValue, source: tuple) -> bool:
        if (value.ip, value.port) == source:
            # check signature
            if self.set_location(value=value):
                # login accepted
                return True
        # response 'SIGN' command with 'ID' and 'ADDR'
        cmd = SignCommand.new(uid=value.id, address=source)
        self.send_command(cmd=cmd, destination=source)
        return True

    def __process_call(self, value: CommandValue, source: tuple) -> bool:
        receiver = self.get_location(uid=value.id)
        if receiver is None or receiver.ip is None:
            # receiver not online
            # respond an empty 'FROM' command to the sender
            cmd = FromCommand.new(uid=value.id)
            self.send_command(cmd=cmd, destination=source)
        else:
            assert receiver.port > 0, 'receiver port error: %s' % receiver
            # receiver is online
            sender = self.get_location(source=source)
            if sender is None:
                # ask sender to login again
                cmd = WhoCommand.new()
                self.send_command(cmd=cmd, destination=source)
            else:
                # send 'fROM' command with sender's location info to the receiver
                cmd = FromCommand.new(location=sender)
                self.send_command(cmd=cmd, destination=(receiver.ip, receiver.port))
                # respond 'FROM' command with receiver's location info to sender
                cmd = FromCommand.new(location=receiver)
                self.send_command(cmd=cmd, destination=source)
        return True

    def process_command(self, cmd: Command, source: tuple) -> bool:
        cmd_type = cmd.type
        cmd_value = cmd.value
        if cmd_type == Hello:
            assert isinstance(cmd_value, LocationValue), 'login cmd error: %s' % cmd_value
            return self.__process_login(value=cmd_value, source=source)
        elif cmd_type == Call:
            assert isinstance(cmd_value, CommandValue), 'call cmd error: %s' % cmd_value
            return self.__process_call(value=cmd_value, source=source)
        else:
            print('unknown command: %s' % cmd)


class Client(Node):

    @abstractmethod
    def say_hi(self, destination: tuple):
        """
        Send 'HI' command to tell the server who you are

        :param destination: server address
        :return:
        """
        pass

    @abstractmethod
    def sign_in(self, value: LocationValue, destination: tuple) -> bool:
        """
        Sign the MAPPED-ADDRESS in the location value with private key

        :param value:       LocationValue contains ID, IP, port
        :param destination: server's address
        :return: False on error
        """
        pass

    def process_command(self, cmd: Command, source: tuple) -> bool:
        cmd_type = cmd.type
        if cmd_type == Who:
            return self.say_hi(destination=source)
        elif cmd_type == Sign:
            cmd_value = cmd.value
            assert isinstance(cmd_value, LocationValue), 'sign cmd error: %s' % cmd_value
            return self.sign_in(value=cmd_value, destination=source)
        else:
            print('unknown command: %s' % cmd)
