# -*- coding: utf-8 -*-
#
#   Finite State Machine
#
#                                Written in 2022 by Moky <albert.moky@gmail.com>
#
# ==============================================================================
# MIT License
#
# Copyright (c) 2022 Albert Moky
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

import threading
import time
import traceback
import weakref
from abc import ABC, abstractmethod
from typing import Set

from .runner import Runnable, Daemon


class Ticker(ABC):

    @abstractmethod
    def tick(self, now: float, delta: float):
        """
        Drive current thread forward

        :param: now - current time (seconds from Jan 1, 1970 UTC)
        :param: delta - seconds from last call
        """
        raise NotImplemented


class Singleton(object):

    __instances = {}

    def __init__(self, cls):
        self.__cls = cls

    def __call__(self, *args, **kwargs):
        cls = self.__cls
        instance = self.__instances.get(cls, None)
        if instance is None:
            instance = cls(*args, **kwargs)
            self.__instances[cls] = instance
        return instance

    def __getattr__(self, key):
        return getattr(self.__cls, key, None)


@Singleton
class Metronome(Runnable):

    MIN_DELTA = 0.1
    MAX_DELTA = 0.125

    def __init__(self):
        super().__init__()
        self.__lock = threading.Lock()
        self.__adding = weakref.WeakSet()
        self.__removing = weakref.WeakSet()
        self.__tickers = weakref.WeakSet()
        # running as daemon
        self.__daemon = Daemon(target=self.run)
        self.__running = False
        self.start()

    @property
    def running(self) -> bool:
        return self.__running

    def start(self):
        if not self.running:
            self.__running = True
            self.__daemon.start()

    def stop(self):
        if self.running:
            self.__running = False
            self.__daemon.stop()

    # Override
    def run(self):
        now = time.time()
        delta = 0
        while self.running:
            # 1. drive all tickers with timestamp
            try:
                self.__drive(now=now, delta=delta)
            except Exception as error:
                print('[Metronome] drive error: %s' % error)
                traceback.print_exc()
            # 2. get new timestamp
            last = now
            now = time.time()
            delta = now - last
            if delta < self.MIN_DELTA:
                # 3. too frequently
                time.sleep(self.MAX_DELTA - delta)
                now = time.time()
                delta = now - last

    def __drive(self, now: float, delta: float):
        tickers = self.tickers
        for item in tickers:
            try:
                item.tick(now=now, delta=delta)
            except Exception as error:
                print('[Metronome] drive ticker error: %s, %s' % (error, item))
                traceback.print_exc()

    @property
    def tickers(self) -> Set[Ticker]:
        with self.__lock:
            for item in self.__adding:
                self.__tickers.add(item)
            self.__adding.clear()
            for item in self.__removing:
                self.__tickers.discard(item)
            self.__removing.clear()
        # OK
        return set(self.__tickers)

    def add(self, ticker: Ticker):
        with self.__lock:
            self.__removing.discard(ticker)
            self.__adding.add(ticker)

    def remove(self, ticker: Ticker):
        with self.__lock:
            self.__adding.discard(ticker)
            self.__removing.add(ticker)
