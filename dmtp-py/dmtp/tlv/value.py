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
from typing import Optional, Union, List, Dict, Iterator, ItemsView, KeysView, ValuesView

from udp.ba import ByteArray, Data
from stun.tlv import VarLength as FieldLength
from stun.tlv import Value as FieldValue
from stun.tlv import RawValue, StringValue, Value8, Value16, Value32

from .tag import StringTag as FieldName
from .field import Field


class MapValue(RawValue, Dict[FieldName, FieldValue]):

    def __init__(self, data: Union[bytes, bytearray, ByteArray], fields: List[Field]):
        super().__init__(data=data)
        self.__dictionary = {}  # FieldName -> FieldValue
        for item in fields:
            self.__dictionary[item.tag] = item.value

    @property
    def dictionary(self) -> dict:
        return self.__dictionary

    def copy_dictionary(self, deep_copy: bool = False) -> dict:
        if deep_copy:
            copy.deepcopy(self.__dictionary)
        else:
            return self.__dictionary.copy()

    def copy(self):
        """ D.copy() -> a shallow copy of D """
        data = self.get_bytes()
        clone = MapValue(data=data, fields=[])
        clone.__dictionary = self.__dictionary.copy()
        return clone

    def get(self, k: FieldName, default: Optional[FieldValue] = None) -> Optional[FieldValue]:
        """ Return the value for key if key is in the dictionary, else default. """
        return self.__dictionary.get(k, default)

    def items(self) -> ItemsView[FieldName, FieldValue]:
        """ D.items() -> a set-like object providing a view on D's items """
        return self.__dictionary.items()

    def keys(self) -> KeysView[FieldName]:
        """ D.keys() -> a set-like object providing a view on D's keys """
        return self.__dictionary.keys()

    def values(self) -> ValuesView[FieldValue]:
        """ D.values() -> an object providing a view on D's values """
        return self.__dictionary.values()

    def __contains__(self, o) -> bool:
        """ True if the dictionary has the specified key, else False. """
        return self.__dictionary.__contains__(o)

    # def __getattribute__(self, name: str) -> Any:
    #     """ Return getattr(self, name). """
    #     if isinstance(name, String):
    #         name = name.string
    #     return self.__dictionary.__getattribute__(name=name)

    def __getitem__(self, k: FieldName) -> FieldValue:
        """ x.__getitem__(y) <==> x[y] """
        return self.__dictionary.__getitem__(k)

    def __eq__(self, o) -> bool:
        """ Return self==value. """
        if isinstance(o, MapValue):
            if self is o:
                return True
            o = o.dictionary
        return self.__dictionary.__eq__(o)

    def __ne__(self, o) -> bool:
        """ Return self!=value. """
        if isinstance(o, MapValue):
            if self is o:
                return False
            o = o.dictionary
        return self.__dictionary.__ne__(o)

    def __ge__(self, other) -> bool:
        """ Return self>=value. """
        pass

    def __gt__(self, other) -> bool:
        """ Return self>value. """
        pass

    def __iter__(self) -> Iterator[FieldName]:
        """ Implement iter(self). """
        return self.__dictionary.__iter__()

    def __len__(self) -> int:
        """ Return len(self). """
        return self.__dictionary.__len__()

    def __le__(self, other) -> bool:
        """ Return self<=value. """
        pass

    def __lt__(self, other) -> bool:
        """ Return self<value. """
        pass

    def __str__(self) -> str:
        """ Return str(self) """
        return self.__dictionary.__str__()

    def __repr__(self) -> str:
        """ Return repr(self). """
        return self.__dictionary.__repr__()

    def __sizeof__(self) -> int:
        """ D.__sizeof__() -> size of D in memory, in bytes """
        return self.__dictionary.__sizeof__()

    __hash__ = None

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
