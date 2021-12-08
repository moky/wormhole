# -*- coding: utf-8 -*-
#
#   SHM: Shared Memory
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

import json
from abc import ABC, abstractmethod
from typing import Optional, Union, Any


class Queue(ABC):

    @abstractmethod
    def push(self, data: Union[bytes, bytearray]) -> bool:
        """ inqueue """
        raise NotImplemented

    @abstractmethod
    def shift(self) -> Union[bytes, bytearray, None]:
        """ dequeue """
        raise NotImplemented


class QueueController:

    def __init__(self, queue: Queue):
        super().__init__()
        self.__queue = queue

    @property
    def queue(self) -> Queue:
        return self.__queue

    def __str__(self) -> str:
        mod = self.__module__
        cname = self.__class__.__name__
        return '<%s>%s</%s module="%s">' % (cname, self.queue, cname, mod)

    def __repr__(self) -> str:
        mod = self.__module__
        cname = self.__class__.__name__
        return '<%s>%s</%s module="%s">' % (cname, self.queue, cname, mod)

    # noinspection PyMethodMayBeStatic
    def _decode(self, data: Any) -> Any:
        # noinspection PyBroadException,PyUnusedLocal
        try:
            s = data.decode('utf-8')
            return json.loads(s)
        except Exception as error:
            # print('[SHM] not json: %s, %s' % (error, data))
            # import traceback
            # traceback.print_exc()
            return data

    # noinspection PyMethodMayBeStatic
    def _encode(self, obj: Optional[Any]) -> Union[bytes, bytearray, None]:
        if obj is None:
            return None
        elif isinstance(obj, bytes) or isinstance(obj, bytearray):
            return obj
        else:
            data = json.dumps(obj)
            return data.encode('utf-8')

    def shift(self) -> Optional[Any]:
        data = self.queue.shift()
        if data is not None:
            return self._decode(data=data)

    def push(self, obj: Optional[Any]) -> bool:
        data = self._encode(obj=obj)
        return self.queue.push(data=data)
