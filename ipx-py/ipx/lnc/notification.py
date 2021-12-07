# -*- coding: utf-8 -*-
#
#   LNC: Local Notification Center
#
#                                Written in 2019 by Moky <albert.moky@gmail.com>
#
# ==============================================================================
# MIT License
#
# Copyright (c) 2019 Albert Moky
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

from typing import Optional, Any


class Notification:
    """ Notification object with name, sender and extra info """

    def __init__(self, name: str, sender: Any, info: dict = None):
        super().__init__()
        self.__name = name
        self.__sender = sender
        self.__info = info

    def __str__(self) -> str:
        clazz = self.__class__.__name__
        return '<%s:%s| sender=%s, info=%s />' % (clazz, self.name, self.sender, self.info)

    def __repr__(self) -> str:
        clazz = self.__class__.__name__
        return '<%s:%s| sender=%s, info=%s />' % (clazz, self.name, self.sender, self.info)

    @property
    def name(self) -> str:
        return self.__name

    @property
    def sender(self) -> Any:
        return self.__sender

    @property
    def info(self) -> Optional[dict]:
        return self.__info

    @info.setter
    def info(self, value: dict):
        self.__info = value
