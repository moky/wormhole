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

import traceback
from weakref import WeakSet
from typing import Any, Dict

from .notification import Notification
from .observer import NotificationObserver


# @Singleton
class NotificationCenter:
    """ Notification dispatcher """

    def __init__(self):
        super().__init__()
        self.__observers: Dict[str, WeakSet] = {}

    def add(self, observer: NotificationObserver, name: str):
        """
        Add observer with notification name

        :param observer: notification observer
        :param name:     notification name
        :return:
        """
        array = self.__observers.get(name)
        if array is None:
            array = WeakSet()
            self.__observers[name] = array
        elif observer in array:
            # already exists
            return
        array.add(observer)

    def __remove(self, observer: NotificationObserver, name: str):
        array = self.__observers.get(name)
        if array is not None:
            array.discard(observer)

    def remove(self, observer: NotificationObserver, name: str = None):
        """
        Remove observer from notification center, no mather what names

        :param observer: notification observer to remove
        :param name:     notification name (if empty, remove from all names)
        :return:
        """
        if name is None:
            keys = self.__observers.keys()
            for item in keys:
                self.__remove(observer=observer, name=item)
        else:
            self.__remove(observer=observer, name=name)

    def post(self, notification: Notification = None,
             name: str = None, sender: Any = None, info: dict = None):
        """
        Post a notification (with name, sender and extra info)

        :param notification: notification object
        :param name:         notification name  (when 'notification' empty)
        :param sender:       notification sender(when 'notification' empty)
        :param info:         extra info         (when 'notification' empty)
        :return:
        """
        if notification is None:
            assert name is not None, 'Notification name empty'
            assert sender is not None, 'Notification sender empty'
            notification = Notification(name=name, sender=sender, info=info)
        # temporary array buffer, used as a snapshot of the state of current observers
        array = self.__observers.get(notification.name)
        if array is not None:
            array = array.copy()
            # call observers one by one
            for observer in array:
                try:
                    assert isinstance(observer, NotificationObserver), 'notification observer error: %s' % observer
                    observer.received_notification(notification=notification)
                except Exception as error:
                    print('[LNC] failed to call notification observer %s: %s' % (observer, error))
                    traceback.print_exc()
