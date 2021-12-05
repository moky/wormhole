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
from typing import Union

from .cache import CycledCache


class SharedMemory:

    def __init__(self, buffer):
        super().__init__()
        self._cache = CycledCache(buffer=buffer, head_length=4)

    @property
    def buffer(self) -> bytes:
        raise NotImplemented

    @property
    def size(self) -> int:
        return len(self.buffer)

    def __str__(self) -> str:
        mod = self.__module__
        cname = self.__class__.__name__
        return '<%s.%s| size=%d buffer=%s />' % (mod, cname, self.size, self.buffer)

    def __repr__(self) -> str:
        mod = self.__module__
        cname = self.__class__.__name__
        return '<%s.%s| size=%d buffer=%s />' % (mod, cname, self.size, self.buffer)

    def get(self) -> Union[str, dict, list, None]:
        data = self._cache.get()
        if data is not None:
            data = data.decode('utf-8')
            return json.loads(data)

    def put(self, o: Union[str, dict, list]) -> bool:
        data = json.dumps(o)
        data = data.encode('utf-8')
        return self._cache.put(data=data)
