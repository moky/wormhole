# -*- coding: utf-8 -*-
#
#   Finite State Machine
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

import time
from abc import ABC, abstractmethod
from threading import Thread
from typing import Optional, Generic

from .machine import S, C, U, T
from .base import BaseMachine


class Runnable(ABC):

    @abstractmethod
    def run(self):
        raise NotImplemented


class AutoMachine(BaseMachine, Runnable, ABC, Generic[C, T, S]):

    def __init__(self, default: str):
        super().__init__(default=default)
        self.__thread: Optional[Thread] = None

    # Override
    def start(self):
        super().start()
        if self.__thread is None:
            self.__thread = Thread(target=self.run)
            self.__thread.start()

    # Override
    def stop(self):
        super().stop()
        t: Thread = self.__thread
        if t is not None:
            t.join()
            self.__thread = None

    # Override
    def run(self):
        self.setup()
        try:
            self.handle()
        finally:
            self.finish()

    def setup(self):
        """ prepare for running """
        pass

    def finish(self):
        """ clean up after run """
        pass

    def handle(self):
        while self.current_state is not None:
            self.tick()
            self.idle()

    # noinspection PyMethodMayBeStatic
    def idle(self):
        time.sleep(0.125)
