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

"""
    Pool
    ~~~~

    Tasks cache pool
"""

from abc import ABC, abstractmethod
from typing import Optional

from .package import Package
from .task import Departure, Arrival


class Pool(ABC):
    """
        Task Pool
        ~~~~~~~~~

        Cache for departure, arrival tasks and message fragments
    """

    #
    #   Departures
    #

    @abstractmethod
    def shift_expired_departure(self) -> Optional[Departure]:
        """
        Gat one departure task from the pool for sending.

        :return: any expiring departure task (removed from pool)
        """
        raise NotImplemented

    @abstractmethod
    def append_departure(self, task: Departure) -> bool:
        """
        Append a departure task into the pool after sent.
        This should be removed after its response received; if timeout, send it
        again and check it's retries counter, when it's still greater than 0,
        put it back to the pool for resending.

        :param task: departure task
        :return: False on failed
        """
        raise NotImplemented

    @abstractmethod
    def delete_departure(self, response: Package, destination: tuple, source: tuple) -> bool:
        """
        Delete the departure task with 'trans_id' in the response.
        If it's a message fragment, check the page offset too.

        :param response:    respond package
        :param destination: remote address
        :param source:      local address
        :return: False on task not found/not finished yet
        """
        raise NotImplemented

    #
    #   Arrivals
    #

    @abstractmethod
    def arrivals_count(self) -> int:
        """
        Check how many arrivals waiting in the pool

        :return: arrivals count
        """
        raise NotImplemented

    @abstractmethod
    def shift_first_arrival(self) -> Optional[Arrival]:
        """
        Get one arrival task from the pool for processing

        :return: the first arrival task (removed from pool)
        """
        raise NotImplemented

    @abstractmethod
    def append_arrival(self, task: Arrival) -> bool:
        """
        Append an arrival task into the pool after received something

        :param task: arrival task
        :return: False on failed
        """
        raise NotImplemented

    #
    #   Fragments Assembling
    #

    @abstractmethod
    def insert_fragment(self, fragment: Package, source: tuple, destination: tuple) -> Optional[Package]:
        """
        Add a fragment package into the pool for MessageFragment received.
        This will just wait until all fragments with the same 'trans_id' received.
        When all fragments received, they will be sorted and combined to the
        original message, and then return the message's data; if there are still
        some fragments missed, return None.

        :param fragment:    message fragment
        :param source:      remote address
        :param destination: local address
        :return: original message package when all fragments received
        """
        raise NotImplemented

    @abstractmethod
    def discard_fragments(self) -> list:
        """
        Remove all expired fragments that belong to the incomplete messages,
        which had waited a long time but still some fragments missed.

        :return: assembling list
        """
        raise NotImplemented
