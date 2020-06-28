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

from .tlv import Field, FieldsValue
from .tlv import VarName, BinaryValue, ByteValue, TimestampValue, StringValue
from .tlv import s_value_parsers


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

    def __init__(self, fields: list, data: bytes=None):
        # envelope
        self.__sender: str = None
        self.__receiver: str = None
        self.__time: int = 0
        self.__type: int = 0
        self.__group: str = None
        # body
        self.__content: bytes = None
        self.__signature: bytes = None
        self.__key: bytes = None
        # attachments
        self.__meta: bytes = None
        self.__profile: bytes = None
        # file in message
        self.__filename: str = None
        super().__init__(fields=fields, data=data)

    @property
    def sender(self) -> str:
        return self.__sender

    @property
    def receiver(self) -> str:
        return self.__receiver

    @property
    def time(self) -> Optional[int]:
        return self.__time

    @property
    def type(self) -> Optional[int]:
        return self.__type

    @property
    def group(self) -> Optional[str]:
        return self.__group

    @property
    def content(self) -> bytes:
        return self.__content

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

    @property
    def filename(self) -> Optional[str]:
        return self.__filename

    def _set_field(self, field: Field):
        f_type = field.tag
        f_value = field.value
        if f_type == MsgSender:
            assert isinstance(f_value, StringValue), 'sender ID error: %s' % f_value
            self.__sender = f_value.string
        elif f_type == MsgReceiver:
            assert isinstance(f_value, StringValue), 'receiver ID error: %s' % f_value
            self.__receiver = f_value.string
        elif f_type == MsgTime:
            assert isinstance(f_value, TimestampValue), 'time error: %s' % f_value
            self.__time = f_value.value
        elif f_type == MsgType:
            assert isinstance(f_value, ByteValue), 'content type error: %s' % f_value
            self.__type = f_value.value
        elif f_type == MsgGroup:
            assert isinstance(f_value, StringValue), 'group ID error: %s' % f_value
            self.__group = f_value.string
        elif f_type == MsgContent:
            assert isinstance(f_value, BinaryValue), 'content data error: %s' % f_value
            self.__content = f_value.data
        elif f_type == MsgSignature:
            assert isinstance(f_value, BinaryValue), 'signature error: %s' % f_value
            self.__signature = f_value.data
        elif f_type == MsgKey:
            assert isinstance(f_value, BinaryValue), 'symmetric key error: %s' % f_value
            self.__key = f_value.data
        elif f_type == MsgMeta:
            assert isinstance(f_value, BinaryValue), 'meta error: %s' % f_value
            self.__meta = f_value.data
        elif f_type == MsgProfile:
            assert isinstance(f_value, BinaryValue), 'profile error: %s' % f_value
            self.__profile = f_value.data
        elif f_type == MsgFilename:
            assert isinstance(f_value, StringValue), 'filename error: %s' % f_value
            self.__filename = f_value.string
        else:
            clazz = self.__class__.__name__
            print('%s> unknown field: %s -> %s' % (clazz, f_type, f_value))

    @classmethod
    def __fetch_msg_field(cls, array: list, info: dict, s: str, name: str, tag: VarName, clazz):
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
        cls.__fetch_msg_field(fields, info, 'S', 'sender', MsgSender, StringValue)
        cls.__fetch_msg_field(fields, info, 'R', 'receiver', MsgReceiver, StringValue)
        cls.__fetch_msg_field(fields, info, 'W', 'time', MsgTime, TimestampValue)
        cls.__fetch_msg_field(fields, info, 'T', 'type', MsgType, ByteValue)
        cls.__fetch_msg_field(fields, info, 'G', 'group', MsgGroup, StringValue)
        # body
        cls.__fetch_msg_field(fields, info, 'D', 'data', MsgContent, BinaryValue)
        cls.__fetch_msg_field(fields, info, 'K', 'key', MsgKey, BinaryValue)
        cls.__fetch_msg_field(fields, info, 'S', 'signature', MsgSignature, BinaryValue)
        # attachments
        cls.__fetch_msg_field(fields, info, 'M', 'meta', MsgMeta, BinaryValue)
        cls.__fetch_msg_field(fields, info, 'P', 'profile', MsgProfile, BinaryValue)
        # file
        cls.__fetch_msg_field(fields, info, 'F', 'filename', MsgFilename, StringValue)
        return cls(fields=fields)


# message field names
MsgSender = VarName('S')
MsgReceiver = VarName('R')
MsgTime = VarName('W')
MsgType = VarName('T')
MsgGroup = VarName('G')

MsgContent = VarName('D')    # message content Data; or file content Data
MsgSignature = VarName('V')  # signature for Verify content data with sender's meta.key
MsgKey = VarName('K')

MsgMeta = VarName('M')
MsgProfile = VarName('P')

MsgFilename = VarName('F')   # Filename

# classes for parsing message
s_value_parsers[MsgSender] = StringValue
s_value_parsers[MsgReceiver] = StringValue
s_value_parsers[MsgTime] = TimestampValue
s_value_parsers[MsgType] = ByteValue
s_value_parsers[MsgGroup] = StringValue

s_value_parsers[MsgContent] = BinaryValue
s_value_parsers[MsgSignature] = BinaryValue
s_value_parsers[MsgKey] = BinaryValue

s_value_parsers[MsgMeta] = BinaryValue
s_value_parsers[MsgProfile] = BinaryValue

s_value_parsers[MsgFilename] = StringValue
