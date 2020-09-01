# -*- coding: utf-8 -*-
#
#   MTP: Message Transfer Protocol
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

from abc import ABC, abstractmethod

from .tlv import Data

from .protocol import TransactionID
from .package import Package


"""
    Topology:

        +-----------------------------------------------+
        |                      APP                      |
        |                 (Peer Handler)                |
        +-----------------------------------------------+
                            |       A
                            |       |
                            V       |
        +---+--------+----------------------------------+
        |   |  Pool  |                                  |        pool:
        |   +--------+         Peer        +--------+   |          -> departures
        |                (Hub Listener)    | Filter |   |          -> arrivals
        +----------------------------------+--------+---+          -> assembling
                            |       A
                            |       |
                            V       |
        +-----------------------------------------------+
        |                      HUB                      |
        +-----------------------------------------------+
"""


class PeerDelegate(ABC):

    #
    #  Send
    #

    @abstractmethod
    def send_data(self, data: Data, destination: tuple, source: tuple) -> int:
        """
        Send data to destination address.

        :param data:        data package to send
        :param destination: remote address
        :param source:      local address
        :return: -1 on error
        """
        raise NotImplemented


class PeerHandler(ABC):

    #
    #  Callbacks
    #

    # @abstractmethod
    def send_command_success(self, sn: TransactionID, destination: tuple, source: tuple):
        """
        Callback for command success.

        :param sn:          transaction ID
        :param destination: remote address
        :param source:      local address
        """
        pass

    # @abstractmethod
    def send_command_timeout(self, sn: TransactionID, destination: tuple, source: tuple):
        """
        Callback for command failed.

        :param sn:          transaction ID
        :param destination: remote address
        :param source:      local address
        """
        pass

    # @abstractmethod
    def send_message_success(self, sn: TransactionID, destination: tuple, source: tuple):
        """
        Callback for message success.

        :param sn:          transaction ID
        :param destination: remote address
        :param source:      local address
        """
        pass

    # @abstractmethod
    def send_message_timeout(self, sn: TransactionID, destination: tuple, source: tuple):
        """
        Callback for message failed.

        :param sn:          transaction ID
        :param destination: remote address
        :param source:      local address
        """
        pass

    #
    #  Received
    #

    @abstractmethod
    def received_command(self, cmd: Data, source: tuple, destination: tuple) -> bool:
        """
        Received command data from source address.

        :param cmd:         command data (package body) received
        :param source:      remote address
        :param destination: local address
        :return: False on error
        """
        raise NotImplemented

    @abstractmethod
    def received_message(self, msg: Data, source: tuple, destination: tuple) -> bool:
        """
        Received message data from source address.

        :param msg:         message data (package body) received
        :param source:      remote address
        :param destination: local address
        :return: False on error
        """
        raise NotImplemented

    # @abstractmethod
    def received_error(self, data: Data, source: tuple, destination: tuple):
        """
        Received error data from source address.

        :param data:        error data (failed to parse) received
        :param source:      remote address
        :param destination: local address
        :return:
        """
        pass

    # @abstractmethod
    # noinspection PyUnusedLocal, PyMethodMayBeStatic
    def check_fragment(self, fragment: Package, source: tuple, destination: tuple) -> bool:
        """
        Check message fragment from the source address, if too many incomplete tasks
        from the same address, return False to reject it to avoid 'DDoS' attack.

        :param fragment:    message fragment
        :param source:      remote address
        :param destination: local address
        :return: False on error
        """
        return True

    # @abstractmethod
    def recycle_fragments(self, fragments: list, source: tuple, destination: tuple):
        """
        Recycle incomplete message fragments from source address.
        (Override for resuming the transaction)

        :param fragments:   fragment packages
        :param source:      remote address
        :param destination: local address
        :return:
        """
        pass
