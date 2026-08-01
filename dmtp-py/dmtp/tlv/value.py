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

import copy
from typing import Optional, Union, Any, List, Tuple
from typing import AbstractSet
from typing import Iterable, Iterator, ValuesView

from udp.ba import ByteArray, Data
from stun.tlv import VarLength as FieldLength
from stun.tlv import Value as FieldValue
from stun.tlv import RawValue, StringValue, Value8, Value16, Value32

from .tag import StringTag as FieldName
from .field import Field


"""
    Generic for Field Map
    ~~~~~~~~~~~~~~~~~~~~~
"""
try:
    import collections.abc as abc
    FieldMap = abc.MutableMapping[FieldName, FieldValue]
except TypeError:
    import typing
    FieldMap = typing.MutableMapping[FieldName, FieldValue]


class MapValue(RawValue, FieldMap):

    def __init__(self, data: Union[bytes, bytearray, ByteArray], fields: List[Field]):
        super().__init__(data=data)
        self.__dictionary: FieldMap = {}  # FieldName -> FieldValue
        for item in fields:
            self.__dictionary[item.tag] = item.value

    def to_map(self) -> FieldMap:
        return self.__dictionary

    def copy_map(self, deep_copy: bool = False) -> FieldMap:
        # info = self.__dictionary
        info = self.to_map()
        if deep_copy:
            copy.deepcopy(info)
        else:
            return dict(info)

    def copy(self):  # -> MapValue:
        """ D.copy() -> a shallow copy of D """
        data = self.get_bytes()
        clone = MapValue(data=data, fields=[])
        clone.__dictionary = dict(self.__dictionary)
        return clone

    def __eq__(self, o: object) -> bool:
        """ Return self==value. """
        if isinstance(o, MapValue):
            if self is o:
                return True
            o = o.to_map()
        return self.__dictionary.__eq__(o)

    def __ne__(self, o: object) -> bool:
        """ Return self!=value. """
        if isinstance(o, MapValue):
            if self is o:
                return False
            o = o.to_map()
        return self.__dictionary.__ne__(o)

    def __repr__(self) -> str:
        """ Return repr(self). """
        return self.__dictionary.__repr__()

    def __str__(self) -> str:
        """ Return str(self) """
        return self.__dictionary.__str__()

    def __sizeof__(self) -> int:
        """ D.__sizeof__() -> size of D in memory, in bytes """
        return self.__dictionary.__sizeof__()

    def __len__(self) -> int:
        """ Return len(self). """
        return self.__dictionary.__len__()

    #
    #   Hashable
    #

    # Override
    def __hash__(self) -> int:
        """ Implement hash(self). """
        return self.__dictionary.__hash__()

    #
    #   Iterable
    #

    # Override
    def __iter__(self) -> Iterator[FieldName]:
        """ Implement iter(self). """
        return self.__dictionary.__iter__()

    #
    #   Mapping
    #

    # Override
    def __getitem__(self, k: FieldName) -> FieldValue:
        """ x.__getitem__(y) <==> x[y] """
        return self.__dictionary.__getitem__(k)

    # Override
    def get(self, k: FieldName, default: Optional[FieldValue] = None) -> Optional[FieldValue]:
        """ Return the value for key if key is in the dictionary, else default. """
        return self.__dictionary.get(k, default)

    # Override
    def items(self) -> AbstractSet[Tuple[FieldName, FieldValue]]:
        """ D.items() -> a set-like object providing a view on D's items """
        return self.__dictionary.items()

    # Override
    def keys(self) -> AbstractSet[FieldName]:
        """ D.keys() -> a set-like object providing a view on D's keys """
        return self.__dictionary.keys()

    # Override
    def values(self) -> ValuesView[FieldValue]:
        """ D.values() -> an object providing a view on D's values """
        return self.__dictionary.values()

    # Override
    def __contains__(self, o: object) -> bool:
        """ True if the dictionary has the specified key, else False. """
        return self.__dictionary.__contains__(o)

    #
    #   MutableMapping
    #

    # Override
    def __setitem__(self, k: FieldName, v: Optional[FieldValue]):
        """ Set self[key] to value. """
        self.__dictionary.__setitem__(k, v)

    # Override
    def __delitem__(self, v: FieldName):
        """ Delete self[key]. """
        self.__dictionary.__delitem__(v)

    # Override
    def clear(self):
        """ D.clear() -> None.  Remove all items from D. """
        self.__dictionary.clear()

    # Override
    def pop(self, k: FieldName, default: Optional[FieldValue] = None) -> Optional[FieldValue]:
        """
        D.pop(k[,d]) -> v, remove specified key and return the corresponding value.
        If key is not found, d is returned if given, otherwise KeyError is raised
        """
        return self.__dictionary.pop(k, default)

    # Override
    def popitem(self) -> Tuple[FieldName, FieldValue]:
        """
        D.popitem() -> (k, v), remove and return some (key, value) pair as a
        2-tuple; but raise KeyError if D is empty.
        """
        return self.__dictionary.popitem()

    # Override
    def setdefault(self, k: FieldName, default: FieldValue = None) -> FieldValue:
        """
        Insert key with a value of default if key is not in the dictionary.

        Return the value for key if key is in the dictionary, else default.
        """
        return self.__dictionary.setdefault(k, default)

    # Override
    def update(self, __m: Union[FieldMap, Iterable[Tuple[str, FieldValue]]], **kwargs: Any):
        """
        D.update([E, ]**F) -> None.  Update D from dict/iterable E and F.
        If E is present and has a .keys() method, then does:  for k in E: D[k] = E[k]
        If E is present and lacks a .keys() method, then does:  for k, v in E: D[k] = v
        In either case, this is followed by: for k in F:  D[k] = F[k]
        """
        self.__dictionary.update(__m, **kwargs)

    #
    #   Getting Values
    #

    def get_binary_value(self, tag: FieldName, default: Optional[bytes] = None) -> Optional[bytes]:
        value = self.get(tag)
        if isinstance(value, RawValue):
            return value.get_bytes()
        else:
            return default

    def get_string_value(self, tag: FieldName, default: Optional[str] = None) -> Optional[str]:
        value = self.get(tag)
        if isinstance(value, StringValue):
            return value.string
        else:
            return default

    def get_int_value(self, tag: FieldName, default: Optional[int] = None) -> Optional[int]:
        value = self.get(tag)
        if isinstance(value, (Value8, Value16, Value32)):
            return value.value
        else:
            return default

    #
    #   Factory methods
    #

    @classmethod
    def from_fields(cls, fields: List[Field]):  # -> MapValue
        """ Create MapValue from fields """
        if fields is None or len(fields) == 0:
            return None
        data = fields[0]
        for i in range(1, len(fields)):
            data = data.concat(fields[i])
        return cls(data=data, fields=fields)

    @classmethod
    def parse(cls, data: Union[bytes, bytearray, ByteArray],
              tag: Optional[FieldName] = None, length: Optional[FieldLength] = None):  # -> MapValue
        if isinstance(data, cls):
            return data
        elif not isinstance(data, ByteArray):
            data = Data(buffer=data)
        fields = Field.parse_fields(data=data)
        return cls(data=data, fields=fields)
