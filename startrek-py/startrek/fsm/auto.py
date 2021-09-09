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
from threading import Thread
from typing import Optional

from .runner import Handler, Runnable
from .machine import S, C, U, T
from .base import BaseMachine


class AutoMachine(BaseMachine[C, T, S], Runnable, Handler):

    def __init__(self, default: str):
        super().__init__(default=default)
        self.__thread: Optional[Thread] = None

    # Override
    def start(self):
        super().start()
        self.__force_stop()
        self.__thread = Thread(target=self.run)
        self.__thread.start()

    def __force_stop(self):
        t: Thread = self.__thread
        if t is not None:
            t.join()
            self.__thread = None

    # Override
    def stop(self):
        super().stop()
        self.__force_stop()

    # Override
    def run(self):
        self.setup()
        try:
            self.handle()
        finally:
            self.finish()

    # Override
    def setup(self):
        """ prepare for running """
        pass

    # Override
    def finish(self):
        """ clean up after run """
        pass

    # Override
    def handle(self):
        while self.current_state is not None:
            self.tick()
            self._idle()

    # noinspection PyMethodMayBeStatic
    def _idle(self):
        time.sleep(0.125)
