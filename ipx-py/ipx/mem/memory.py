# -*- coding: utf-8 -*-
#
#   SHM: Shared Memory
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
from typing import Union, Optional


class Memory(ABC):
    """ Memory Access """

    @property
    def size(self) -> int:
        """ get size for available zone """
        raise NotImplemented

    @abstractmethod
    def get_byte(self, index: int) -> int:
        """ get item value with position """
        raise NotImplemented

    @abstractmethod
    def get_bytes(self, start: int = 0, end: int = None) -> Optional[bytes]:
        """ get slice with range [start, end) """
        raise NotImplemented

    @abstractmethod
    def set_byte(self, index: int, value: int):
        """ set item value with position """
        raise NotImplemented

    @abstractmethod
    def update(self, index: int, source: Union[bytes, bytearray], start: int = 0, end: int = None):
        """ update buffer with range [index, index + end - start)
            if end is None, end = len(source)
        """
        raise NotImplemented

    def _buffer_to_string(self) -> str:
        buffer = self.get_bytes()
        size = len(buffer)
        if size < 128:
            return str(buffer)
        else:
            return str(buffer[:120]) + '...' + str(buffer[-8:])

    def __str__(self) -> str:
        mod = self.__module__
        cname = self.__class__.__name__
        buffer = self._buffer_to_string()
        return '<%s size=%d>\n%s\n</%s module="%s">' % (cname, self.size, buffer, cname, mod)

    def __repr__(self) -> str:
        mod = self.__module__
        cname = self.__class__.__name__
        buffer = self._buffer_to_string()
        return '<%s size=%d>\n%s\n</%s module="%s">' % (cname, self.size, buffer, cname, mod)


class MemoryPool(ABC):
    """ FIFO Memory Pool """

    @property
    def memory(self) -> Memory:
        """ memory access """
        raise NotImplemented

    @property
    def capacity(self) -> int:
        """ total spaces for data """
        raise NotImplemented

    @property
    def available(self) -> int:
        """ occupied data length """
        raise NotImplemented

    @property
    def spaces(self) -> int:
        """ empty spaces for incoming data """
        return self.capacity - self.available

    @property
    def is_empty(self) -> bool:
        """ available == 0 """
        raise NotImplemented

    @property
    def is_full(self) -> bool:
        """ spaces == 0 """
        raise NotImplemented

    def __str__(self) -> str:
        mod = self.__module__
        cname = self.__class__.__name__
        return '<%s capacity=%d available=%d>\n%s\n</%s module="%s">'\
               % (cname, self.capacity, self.available, self.memory, cname, mod)

    def __repr__(self) -> str:
        mod = self.__module__
        cname = self.__class__.__name__
        return '<%s capacity=%d available=%d>\n%s\n</%s module="%s">'\
               % (cname, self.capacity, self.available, self.memory, cname, mod)

    @abstractmethod
    def peek(self, length: int) -> Union[bytes, bytearray, None]:
        """ get (not remove) data from buffer, None on empty """
        raise NotImplemented

    @abstractmethod
    def read(self, length: int) -> Union[bytes, bytearray, None]:
        """ get (and remove) data with length from buffer, None on empty """
        raise NotImplemented

    @abstractmethod
    def write(self, data: Union[bytes, bytearray]) -> bool:
        """ put data into buffer, False on full """
        raise NotImplemented


def int_from_bytes(data: Union[bytes, bytearray]) -> int:
    return int.from_bytes(bytes=data, byteorder='big', signed=False)


def int_to_bytes(value: int, length: int = 4) -> Optional[bytes]:
    return value.to_bytes(length=length, byteorder='big', signed=False)
