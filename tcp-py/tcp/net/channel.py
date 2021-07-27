# -*- coding: utf-8 -*-
#
#   TCP: Transmission Control Protocol
#
#                                Written in 2021 by Moky <albert.moky@gmail.com>
#
# ==============================================================================
# MIT License
#
# Copyright (c) 2021 Albert Moky
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


class Channel(ABC):

    @abstractmethod
    @property
    def opened(self) -> bool:
        """ is_open() """
        raise NotImplemented

    @abstractmethod
    @property
    def bound(self) -> bool:
        """ is_bound() """
        raise NotImplemented

    @abstractmethod
    def close(self):
        raise NotImplemented

    #
    #   Byte Channel
    #

    @abstractmethod
    def read(self, max_len: int) -> bytes:
        raise NotImplemented

    @abstractmethod
    def write(self, data: bytes) -> int:
        raise NotImplemented

    #
    #   Selectable Channel
    #

    @abstractmethod
    def configure_blocking(self, blocking: bool):
        raise NotImplemented

    @abstractmethod
    @property
    def blocking(self) -> bool:
        """ is_blocking() """
        raise NotImplemented

    #
    #   Network Channel
    #

    @abstractmethod
    def bind(self, host: str, port: int):
        raise NotImplemented

    @abstractmethod
    @property
    def local_address(self) -> Optional[tuple]:  # (str, int)
        raise NotImplemented

    #
    #   Socket/Datagram Channel
    #

    @abstractmethod
    @property
    def connected(self) -> bool:
        """ is_connected() """
        raise NotImplemented

    @abstractmethod
    def connect(self, host: str, port: int):
        raise NotImplemented

    @abstractmethod
    @property
    def remote_address(self) -> Optional[tuple]:  # (str, int)
        raise NotImplemented

    #
    #   Datagram Channel
    #

    @abstractmethod
    def disconnect(self):
        raise NotImplemented

    @abstractmethod
    def receive(self, max_len: int) -> (bytes, tuple):
        raise NotImplemented

    @abstractmethod
    def send(self, data: bytes, target: tuple) -> int:
        raise NotImplemented