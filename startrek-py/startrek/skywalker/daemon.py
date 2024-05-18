# -*- coding: utf-8 -*-
#
#   Finite State Machine
#
#                                Written in 2024 by Moky <albert.moky@gmail.com>
#
# ==============================================================================
# MIT License
#
# Copyright (c) 2024 Albert Moky
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
import weakref
from threading import Thread
from typing import Optional

from .runner import Runnable, Runner


class Daemon:
    """ Daemon thread """

    def __init__(self, target: Runnable):
        super().__init__()
        self.__target = weakref.ref(target)
        self.__thread: Optional[Thread] = None

    @property  # protected
    def target(self) -> Optional[Runnable]:
        ref = self.__target
        if ref is not None:
            return ref()

    @property  # protected
    def thread(self) -> Optional[Thread]:
        return self.__thread

    @property
    def alive(self) -> bool:
        """ Get background thread status """
        thr = self.__thread
        if thr is not None:
            return thr.is_alive()

    def start(self):
        """ Run the target in background thread """
        self.__force_stop()
        target = self.target
        if target is not None:
            thr = Runner.async_thread(coro=target.run())
            thr.start()
            self.__thread = thr

    def stop(self):
        """ Stop the background thread """
        self.__force_stop()

    def __del__(self):
        self.__force_stop()

    def __force_stop(self):
        # kill background thread
        thr = self.__thread
        if thr is not None:
            self.__thread = None
            self._join(thr=thr)

    def _join(self, thr: Thread):
        # Waits at most seconds for this thread to die.
        # A timeout of 0 means to wait forever.
        self.join(thr=thr, timeout=2.0)

    @classmethod
    def join(cls, thr: Thread, timeout: float = None):
        """ Stop the thread """
        try:
            if thr.is_alive():
                thr.join(timeout=timeout)
        except RuntimeError as error:
            print('[Daemon] failed to join thread: %s, timeout: %d' % (error, timeout))
            traceback.print_exc()
