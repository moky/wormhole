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

    def __init__(self, default: str, daemon: bool = False):
        super().__init__(default=default)
        # running thread
        self.__thread: Optional[Thread] = None
        self.__running = False
        self.__daemon = daemon

    @property
    def running(self) -> bool:
        return self.__running

    # Override
    def start(self):
        self.__restart()
        super().start()

    def __restart(self):
        self.__force_stop()
        self.__running = True
        t = Thread(target=self.run, daemon=self.__daemon)
        self.__thread = t
        t.start()

    def __force_stop(self):
        self.__running = False
        t: Thread = self.__thread
        if t is not None:
            # waiting 2 seconds for stopping the thread
            self.__thread = None
            t.join(timeout=2.0)

    # Override
    def stop(self):
        if self.__running:
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
        while self.running:
            self.tick()
            self._idle()

    # noinspection PyMethodMayBeStatic
    def _idle(self):
        time.sleep(0.125)
