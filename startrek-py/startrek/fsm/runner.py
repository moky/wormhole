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


class Processor(ABC):

    @abstractmethod
    def process(self) -> bool:
        """
        Do the job

        :return: False on nothing to do
        """
        raise NotImplemented


class Handler(ABC):

    @abstractmethod
    def setup(self):
        """ Prepare for Handling """
        raise NotImplemented
    
    @abstractmethod
    def handle(self):
        """ Handling run loop """
        raise NotImplemented

    @abstractmethod
    def finish(self):
        """ Cleanup after handled """
        raise NotImplemented


class Runnable(ABC):

    @abstractmethod
    def run(self):
        """ Run in a thread """
        raise NotImplemented


class Runner(Runnable, Handler, Processor, ABC):
    """
        Runner
        ~~~~~~

        @abstract method:
            - process()
    """

    def __init__(self):
        super().__init__()
        self.__running = False

    @property
    def running(self) -> bool:
        return self.__running

    def stop(self):
        self.__running = False

    # Override
    def run(self):
        self.setup()
        try:
            self.handle()
        finally:
            self.finish()

    # Override
    def setup(self):
        self.__running = True

    # Override
    def handle(self):
        while self.running:
            if not self.process():
                self._idle()

    # Override
    def finish(self):
        self.__running = False

    # noinspection PyMethodMayBeStatic
    def _idle(self):
        time.sleep(0.125)


class Daemon:

    def __init__(self, target, daemonic: bool = True):
        super().__init__()
        self.__target = target
        self.__daemon = daemonic
        self.__thread = None
        self.__timeout = 1.0

    @property
    def timeout(self) -> float:
        return self.__timeout

    @timeout.setter
    def timeout(self, waiting: float):
        self.__timeout = waiting

    @property
    def alive(self) -> bool:
        thr = self.__thread
        if thr is not None:
            return thr.is_alive()

    def start(self) -> Thread:
        self.__force_stop()
        thr = Thread(target=self.__target, daemon=self.__daemon)
        self.__thread = thr
        thr.start()
        return thr

    def __force_stop(self):
        thr: Thread = self.__thread
        if thr is not None:
            self.__thread = None
            try:
                thr.join(timeout=self.timeout)
            except RuntimeError as error:
                print('[ERROR] failed to join thread: %s' % error)

    def stop(self):
        self.__force_stop()
