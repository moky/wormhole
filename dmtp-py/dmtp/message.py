# -*- coding: utf-8 -*-
#
#   DMTP: Direct Message Transfer Protocol
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

from typing import Optional

from udp.tlv import Data

from .tlv import Field, FieldName, FieldValue
from .values import FieldsValue, BinaryValue, TypeValue, TimestampValue, StringValue


"""
    Message
    ~~~~~~~
    
        Fields:
        
            <Envelope>
            S - Sender
            R - Receiver
            W - Time (OPTIONAL)
            
            T - msg Type (OPTIONAL)
            G - Group ID (OPTIONAL)
            
            <Body>
            D - content Data
            V - signature, Verify it with content data and sender's meta.key
            K - symmetric Key for en/decrypt content data (OPTIONAL)
            
            <Attachments>
            M - sender's Meta info (OPTIONAL)
            P - sender's Profile info (OPTIONAL)
    
    File
    ~~~~
    
        Fields:
            
            F - Filename
            D - file content Data
            
            S - Sender (OPTIONAL)
            R - Receiver (OPTIONAL)
            V - signature (OPTIONAL)
            K - symmetric key (OPTIONAL)
"""


class Message(FieldsValue):

    def __init__(self, fields: list, data: Data=None):
        super().__init__(fields=fields, data=data)
        # envelope
        self.__sender: str = None
        self.__receiver: str = None
        self.__time: int = None
        self.__type: int = None
        self.__group: str = None
        # body
        self.__content: Data = None
        self.__signature: Data = None
        self.__key: Data = None
        # attachments
        self.__meta: Data = None
        self.__profile: Data = None
        # file in message
        self.__filename: str = None

    @property
    def sender(self) -> str:
        if self.__sender is None:
            self.__sender = self._get_string_value(self.SENDER)
        return self.__sender

    @property
    def receiver(self) -> str:
        if self.__receiver is None:
            self.__receiver = self._get_string_value(self.RECEIVER)
        return self.__receiver

    @property
    def time(self) -> Optional[int]:
        if self.__time is None:
            self.__time = self._get_timestamp_value(self.TIME, 0)
        return self.__time

    @property
    def type(self) -> Optional[int]:
        if self.__type is None:
            self.__type = self._get_type_value(self.TYPE, 0)
        return self.__type

    @property
    def group(self) -> Optional[str]:
        if self.__group is None:
            self.__group = self._get_string_value(self.GROUP)
        return self.__group

    @property
    def content(self) -> Data:
        if self.__content is None:
            self.__content = self._get_binary_value(self.CONTENT)
        return self.__content

    @property
    def signature(self) -> Data:
        if self.__signature is None:
            self.__signature = self._get_binary_value(self.SIGNATURE)
        return self.__signature

    @property
    def key(self) -> Optional[Data]:
        if self.__key is None:
            self.__key = self._get_binary_value(self.KEY)
        return self.__key

    @property
    def meta(self) -> Optional[Data]:
        if self.__meta is None:
            self.__meta = self._get_binary_value(self.META)
        return self.__meta

    @property
    def profile(self) -> Optional[Data]:
        if self.__profile is None:
            self.__profile = self._get_binary_value(self.PROFILE)
        return self.__profile

    @property
    def filename(self) -> Optional[str]:
        if self.__filename is None:
            self.__filename = self._get_string_value(self.FILENAME)
        return self.__filename

    @classmethod
    def parse(cls, data: Data, tag: FieldName=None, length=None):
        fields = Field.parse_all(data=data)
        assert len(fields) > 0, 'message error: %s' % data
        return Message(fields=fields, data=data)

    @classmethod
    def __fetch_msg_field(cls, array: list, info: dict, s: str, name: str, tag: FieldName, clazz):
        value = info.get(name)
        if value is None:
            value = info.get(s)
            if value is None:
                # no this field
                return None
        if not isinstance(value, clazz):
            value = clazz(value)
        field = Field(tag=tag, value=value)
        array.append(field)

    @classmethod
    def new(cls, info: dict):
        fields = []
        # envelope
        cls.__fetch_msg_field(fields, info, 'S', 'sender', cls.SENDER, StringValue)
        cls.__fetch_msg_field(fields, info, 'R', 'receiver', cls.RECEIVER, StringValue)
        cls.__fetch_msg_field(fields, info, 'W', 'time', cls.TIME, TimestampValue)
        cls.__fetch_msg_field(fields, info, 'T', 'type', cls.TYPE, TypeValue)
        cls.__fetch_msg_field(fields, info, 'G', 'group', cls.GROUP, StringValue)
        # body
        cls.__fetch_msg_field(fields, info, 'D', 'data', cls.CONTENT, BinaryValue)
        cls.__fetch_msg_field(fields, info, 'V', 'signature', cls.SIGNATURE, BinaryValue)
        cls.__fetch_msg_field(fields, info, 'K', 'key', cls.KEY, BinaryValue)
        # attachments
        cls.__fetch_msg_field(fields, info, 'M', 'meta', cls.META, BinaryValue)
        cls.__fetch_msg_field(fields, info, 'P', 'profile', cls.PROFILE, BinaryValue)
        # file
        cls.__fetch_msg_field(fields, info, 'F', 'filename', cls.FILENAME, StringValue)
        # create message with fields
        return cls(fields=fields)

    # message field names
    SENDER = FieldName(name='S')     # sender ID
    RECEIVER = FieldName(name='R')   # receiver ID
    TIME = FieldName(name='W')       # message time
    TYPE = FieldName(name='T')       # message type
    GROUP = FieldName(name='G')      # group ID

    CONTENT = FieldName(name='D')    # message content Data; or file content Data
    SIGNATURE = FieldName(name='V')  # signature for Verify content data with sender's meta.key
    KEY = FieldName(name='K')        # encryption key (symmetric key data encrypted by public key)

    META = FieldName(name='M')       # meta info
    PROFILE = FieldName(name='P')    # profile

    FILENAME = FieldName(name='F')   # Filename


# classes for parsing message
FieldValue.register(tag=Message.SENDER, value_class=StringValue)
FieldValue.register(tag=Message.RECEIVER, value_class=StringValue)
FieldValue.register(tag=Message.TIME, value_class=TimestampValue)
FieldValue.register(tag=Message.TYPE, value_class=TypeValue)
FieldValue.register(tag=Message.GROUP, value_class=StringValue)

FieldValue.register(tag=Message.CONTENT, value_class=BinaryValue)
FieldValue.register(tag=Message.SIGNATURE, value_class=BinaryValue)
FieldValue.register(tag=Message.KEY, value_class=BinaryValue)

FieldValue.register(tag=Message.META, value_class=BinaryValue)
FieldValue.register(tag=Message.PROFILE, value_class=BinaryValue)

FieldValue.register(tag=Message.FILENAME, value_class=StringValue)
