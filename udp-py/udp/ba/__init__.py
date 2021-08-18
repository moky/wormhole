# -*- coding: utf-8 -*-
#
#   BA: Byte Array
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
    Byte Array
    ~~~~~~~~~~
"""

from .array import ByteArray, MutableByteArray
from .array import Endian, IntegerData
from .helper import *

from .data import Data
from .mutable import MutableData
from .integer import IntData, UInt8Data, UInt16Data, UInt32Data, VarIntData

from .convert import Convert

name = "BA"

__author__ = 'Albert Moky'

__all__ = [
    'ByteArray', 'MutableByteArray',
    'Endian', 'IntegerData',

    'Data', 'MutableData',
    'IntData', 'UInt8Data', 'UInt16Data', 'UInt32Data', 'VarIntData',
    'Convert',
]
