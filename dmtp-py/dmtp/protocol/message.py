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

from typing import Optional, Union, List

from udp.ba import ByteArray

from ..tlv import Field, FieldName
from ..tlv import MapValue, StringValue, BinaryValue, TypeValue, TimestampValue


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
            D - content data
            V - signature, Verify it with content data and sender's meta.key
            K - symmetric Key for en/decrypt content data (OPTIONAL)
            
            <Attachments>
            M - sender's Meta info (OPTIONAL)
            P - sender's Profile info (OPTIONAL)
    
    File
    ~~~~
    
        Fields:
            
            F - Filename
            D - file content data
            
            S - Sender (OPTIONAL)
            R - Receiver (OPTIONAL)
            V - signature (OPTIONAL)
            K - symmetric key (OPTIONAL)
"""


class Message(MapValue):

    def __init__(self, data: Union[bytes, bytearray, ByteArray], fields: List[Field]):
        super().__init__(data=data, fields=fields)
        # envelope
        self.__sender: Optional[str] = None
        self.__receiver: Optional[str] = None
        self.__time: Optional[int] = None
        self.__type: Optional[int] = None
        self.__group: Optional[str] = None
        # body
        self.__content: Optional[bytes] = None
        self.__signature: Optional[bytes] = None
        self.__key: Optional[bytes] = None
        # attachments
        self.__meta: Optional[bytes] = None
        self.__profile: Optional[bytes] = None
        # file in message
        self.__filename: Optional[str] = None

    @property
    def sender(self) -> str:
        if self.__sender is None:
            self.__sender = self.get_string_value(tag=self.SENDER)
        return self.__sender

    @property
    def receiver(self) -> str:
        if self.__receiver is None:
            self.__receiver = self.get_string_value(tag=self.RECEIVER)
        return self.__receiver

    @property
    def time(self) -> int:
        if self.__time is None:
            self.__time = self.get_int_value(tag=self.TIME)
        return self.__time

    @property
    def type(self) -> Optional[int]:
        if self.__type is None:
            self.__type = self.get_int_value(tag=self.TYPE)
        return self.__type

    @property
    def group(self) -> Optional[str]:
        if self.__group is None:
            self.__group = self.get_string_value(tag=self.GROUP)
        return self.__group

    @property
    def content(self) -> bytes:
        if self.__content is None:
            self.__content = self.get_binary_value(tag=self.CONTENT)
        return self.__content

    @property
    def signature(self) -> bytes:
        if self.__signature is None:
            self.__signature = self.get_binary_value(tag=self.SIGNATURE)
        return self.__signature

    @property
    def key(self) -> Optional[bytes]:
        if self.__key is None:
            self.__key = self.get_binary_value(tag=self.KEY)
        return self.__key

    @property
    def meta(self) -> Optional[bytes]:
        if self.__meta is None:
            self.__meta = self.get_binary_value(tag=self.META)
        return self.__meta

    @property
    def visa(self) -> Optional[bytes]:
        if self.__profile is None:
            self.__profile = self.get_binary_value(tag=self.VISA)
        return self.__profile

    @property
    def filename(self) -> Optional[str]:
        if self.__filename is None:
            self.__filename = self.get_string_value(tag=self.FILENAME)
        return self.__filename

    # @classmethod
    # def parse(cls, data: Union[bytes, bytearray, ByteArray],
    #           tag: Optional[FieldName] = None, length: Optional[VarLength] = None):  # -> Message
    #     return super().parse(data=data, tag=tag, length=length)

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
        field = Field.new(tag=tag, value=value)
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
        cls.__fetch_msg_field(fields, info, 'P', 'visa', cls.VISA, BinaryValue)
        # file
        cls.__fetch_msg_field(fields, info, 'F', 'filename', cls.FILENAME, StringValue)
        # create message with fields
        return cls.from_fields(fields=fields)

    # message field names
    SENDER = FieldName.from_str(name='S')     # sender ID
    RECEIVER = FieldName.from_str(name='R')   # receiver ID
    TIME = FieldName.from_str(name='W')       # message time
    TYPE = FieldName.from_str(name='T')       # message type
    GROUP = FieldName.from_str(name='G')      # group ID

    CONTENT = FieldName.from_str(name='D')    # message content data; or file content data
    SIGNATURE = FieldName.from_str(name='V')  # signature for Verify content data with sender's meta.key
    KEY = FieldName.from_str(name='K')        # encryption key (symmetric key data encrypted by public key)

    META = FieldName.from_str(name='M')       # meta info
    VISA = FieldName.from_str(name='P')       # visa (profile)

    FILENAME = FieldName.from_str(name='F')   # Filename
