# -*- coding: utf-8 -*-
#
#   DMTP: Direct Message Transfer Protocol
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

from typing import Union

from udp.ba import ByteArray, Data, IntegerData
from stun.tlv import VarTag


class StringTag(VarTag):

    def __init__(self, data: Union[bytes, bytearray, ByteArray], length: IntegerData, content: ByteArray):
        super().__init__(data=data, length=length, content=content)
        self.__name = content.get_bytes().decode('utf-8')

    def __str__(self) -> str:
        return self.__name

    def __repr__(self) -> str:
        return self.__name

    @property
    def name(self) -> str:
        return self.__name

    @classmethod
    def from_str(cls, name: str):  # -> StringTag
        data = name.encode('utf-8')
        content = Data(buffer=data)
        return cls.new(content=content)

    # @classmethod
    # def parse(cls, data: Union[bytes, bytearray, ByteArray]):  # -> StringTag
    #     return super().parse(data=data)
