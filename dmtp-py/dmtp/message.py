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

from .tlv import *


"""
    Message
    ~~~~~~~

    Fields:
    
        <Envelope>
        S - Sender
        R - Receiver
        W - Time (OPTIONAL)
        
        T - content Type (OPTIONAL)
        G - Group ID (OPTIONAL)
        
        <Body>
        D - content Data
        V - signature, Verify it with content data and sender's meta.key
        K - symmetric Key for en/decrypt content data (OPTIONAL)
        
        <Attachments>
        M - sender's Meta info (OPTIONAL)
        P - sender's Profile info (OPTIONAL)
"""


class Message(FieldsValue):

    def __init__(self, fields: list, data: bytes=None):
        self.__sender: str = None
        self.__receiver: str = None
        self.__time: int = 0
        self.__type: int = 0
        self.__group: str = None

        self.__data: bytes = None
        self.__signature: bytes = None
        self.__key: bytes = None

        self.__meta: bytes = None
        self.__profile: bytes = None
        super().__init__(fields=fields, data=data)

    @property
    def sender(self) -> str:
        return self.__sender

    @property
    def receiver(self) -> str:
        return self.__receiver

    @property
    def time(self) -> int:
        return self.__time

    @property
    def type(self) -> Optional[int]:
        return self.__type

    @property
    def group(self) -> Optional[str]:
        return self.__group

    @property
    def data(self) -> bytes:
        return self.__data

    @property
    def signature(self) -> bytes:
        return self.__signature

    @property
    def key(self) -> Optional[bytes]:
        return self.__key

    @property
    def meta(self) -> Optional[bytes]:
        return self.__meta

    @property
    def profile(self) -> Optional[bytes]:
        return self.__profile

    def _set_field(self, field: Field):
        f_type = field.type
        f_value = field.value
        if f_type == 'S':
            assert isinstance(f_value, StringValue), 'sender ID error: %s' % f_value
            self.__sender = f_value.string
        elif f_type == 'R':
            assert isinstance(f_value, StringValue), 'receiver ID error: %s' % f_value
            self.__receiver = f_value.string
        elif f_type == 'W':
            assert isinstance(f_value, TimestampValue), 'time error: %s' % f_value
            self.__time = f_value.value
        elif f_type == 'T':
            assert isinstance(f_value, ByteValue), 'content type error: %s' % f_value
            self.__type = f_value.value
        elif f_type == 'G':
            assert isinstance(f_value, StringValue), 'group ID error: %s' % f_value
            self.__group = f_value.string
        elif f_type == 'D':
            assert isinstance(f_value, BinaryValue), 'content data error: %s' % f_value
            self.__data = f_value.data
        elif f_type == 'V':
            assert isinstance(f_value, BinaryValue), 'signature error: %s' % f_value
            self.__signature = f_value.data
        elif f_type == 'K':
            assert isinstance(f_value, BinaryValue), 'symmetric key error: %s' % f_value
            self.__key = f_value.data
        elif f_type == 'M':
            assert isinstance(f_value, BinaryValue), 'meta error: %s' % f_value
            self.__meta = f_value.data
        elif f_type == 'P':
            assert isinstance(f_value, BinaryValue), 'profile error: %s' % f_value
            self.__profile = f_value.data
        else:
            print('unknown field: %s -> %s' % (f_type, f_value))


# classes for parsing message
s_value_parsers['S'] = StringValue     # Sender
s_value_parsers['R'] = StringValue     # Receiver
s_value_parsers['W'] = TimestampValue  # When
s_value_parsers['T'] = ByteValue       # content Type
s_value_parsers['G'] = StringValue     # Group ID

s_value_parsers['D'] = BinaryValue     # content Data
s_value_parsers['V'] = BinaryValue     # signature for Verify content data with sender's meta.key
s_value_parsers['K'] = BinaryValue     # Key

s_value_parsers['M'] = BinaryValue     # Meta info
s_value_parsers['P'] = BinaryValue     # Profile info
