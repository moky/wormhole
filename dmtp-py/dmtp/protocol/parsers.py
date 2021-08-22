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

from udp.ba import ByteArray
from stun import MappedAddressValue, SourceAddressValue

from ..tlv import Field, FieldName, FieldLength, FieldValue
from ..tlv import ValueParser
from ..tlv import StringValue, BinaryValue, TypeValue, TimestampValue

from .address import RelayedAddressValue
from .values import CommandValue, LocationValue
from .command import Command
from .message import Message


#
#  Default Value Parser
#
class DefaultValueParser(ValueParser[FieldName, FieldLength, FieldValue]):

    def __init__(self, clazz):
        super().__init__()
        self.__clazz = clazz

    def parse_value(self, data: ByteArray, tag: FieldName, length: FieldLength) -> Optional[FieldValue]:
        return self.__clazz.parse(data=data, tag=tag, length=length)


#
#  Parsers for fields
#
Field.register(tag=Command.HELLO, parser=DefaultValueParser(LocationValue))
Field.register(tag=Command.SIGN, parser=DefaultValueParser(LocationValue))
Field.register(tag=Command.CALL, parser=DefaultValueParser(CommandValue))
Field.register(tag=Command.FROM, parser=DefaultValueParser(LocationValue))
Field.register(tag=Command.BYE, parser=DefaultValueParser(LocationValue))

Field.register(tag=Field.ID, parser=DefaultValueParser(StringValue))
Field.register(tag=Field.SOURCE_ADDRESS, parser=DefaultValueParser(SourceAddressValue))
Field.register(tag=Field.MAPPED_ADDRESS, parser=DefaultValueParser(MappedAddressValue))
Field.register(tag=Field.RELAYED_ADDRESS, parser=DefaultValueParser(RelayedAddressValue))
Field.register(tag=Field.TIME, parser=DefaultValueParser(TimestampValue))
Field.register(tag=Field.SIGNATURE, parser=DefaultValueParser(BinaryValue))
Field.register(tag=Field.NAT, parser=DefaultValueParser(StringValue))

#
#  Parsers for message
#
Field.register(tag=Message.SENDER, parser=DefaultValueParser(StringValue))
Field.register(tag=Message.RECEIVER, parser=DefaultValueParser(StringValue))
Field.register(tag=Message.TIME, parser=DefaultValueParser(TimestampValue))
Field.register(tag=Message.TYPE, parser=DefaultValueParser(TypeValue))
Field.register(tag=Message.GROUP, parser=DefaultValueParser(StringValue))

Field.register(tag=Message.CONTENT, parser=DefaultValueParser(BinaryValue))
Field.register(tag=Message.SIGNATURE, parser=DefaultValueParser(BinaryValue))
Field.register(tag=Message.KEY, parser=DefaultValueParser(BinaryValue))

Field.register(tag=Message.META, parser=DefaultValueParser(BinaryValue))
Field.register(tag=Message.VISA, parser=DefaultValueParser(BinaryValue))

Field.register(tag=Message.FILENAME, parser=DefaultValueParser(StringValue))
