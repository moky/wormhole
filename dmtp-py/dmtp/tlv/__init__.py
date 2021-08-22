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

from stun.tlv import Tag, TagParser
from stun.tlv import Tag8, Tag16, Tag32, VarTag
from stun.tlv import Length, LengthParser
from stun.tlv import Length8, Length16, Length32, VarLength
from stun.tlv import Value, ValueParser
from stun.tlv import Value8, Value16, Value32, RawValue, StringValue
from stun.tlv import Entry, EntryParser
from stun.tlv import Triad, Parser

from .field import Field, FieldParser
from .tag import StringTag as FieldName
from .value import FieldLength, FieldValue
from .value import MapValue
from .value import Value8 as TypeValue
from .value import Value32 as TimestampValue
from .value import RawValue as BinaryValue

name = "TLV"

__author__ = 'Albert Moky'

__all__ = [

    'Tag', 'TagParser',
    'Length', 'LengthParser',
    'Value', 'ValueParser',
    'Entry', 'EntryParser',

    'Tag8', 'Tag16', 'Tag32', 'VarTag',
    'Length8', 'Length16', 'Length32', 'VarLength',
    'Value8', 'Value16', 'Value32', 'RawValue', 'StringValue',
    'Triad', 'Parser',

    'Field', 'FieldParser',
    'FieldName', 'FieldLength', 'FieldValue',
    'MapValue', 'TypeValue', 'TimestampValue', 'BinaryValue',
]
