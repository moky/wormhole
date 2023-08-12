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
import traceback
from abc import ABC, abstractmethod
from threading import Thread
from typing import Optional


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

    # Frames Per Second
    # ~~~~~~~~~~~~~~~~~
    # (1) The human eye can process 10-12 still images per second,
    #     and the dynamic compensation function can also deceive us.
    # (2) At a frame rate of 12fps or lower, we can quickly distinguish between
    #     a pile of still images and not animations.
    # (3) Once the playback rate (frames per second) of the images reaches 16-24 fps,
    #     our brain will assume that these images are a continuously moving scene
    #     and will appear like the effect of a movie.
    # (4) At 24fps, there is a feeling of 'motion blur',
    #     while at 60fps, the image is the smoothest and cleanest.
    INTERVAL_SLOW = 1.0/10
    INTERVAL_NORMAL = 1.0/25
    INTERVAL_FAST = 1.0/60

    def __init__(self, interval: float):
        super().__init__()
        assert interval > 0, 'interval error: %s' % interval
        self.__interval = interval
        self.__running = False

    @property
    def interval(self) -> float:
        return self.__interval

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
                # if nothing to do now, return False here
                # to let the thread have a rest.
                self._idle()

    # Override
    def finish(self):
        self.__running = False

    def _idle(self):
        time.sleep(self.interval)

    @abstractmethod
    def process(self) -> bool:
        raise NotImplemented


class Daemon:

    def __init__(self, target, daemonic: bool = True):
        super().__init__()
        self.__target = target  # Callable
        self.__daemon = daemonic
        self.__thread: Optional[Thread] = None

    @property
    def alive(self) -> bool:
        thr = self.__thread
        if thr is not None:
            return thr.is_alive()

    def start(self):
        self.__force_stop()
        thr = Thread(target=self.__target, daemon=self.__daemon)
        thr.start()
        self.__thread = thr

    def stop(self):
        self.__force_stop()

    def __force_stop(self):
        thr = self.__thread
        if thr is not None:
            self.__thread = None
            self._join(thr=thr)

    def _join(self, thr: Thread):
        # Waits at most seconds for this thread to die.
        # A timeout of 0 means to wait forever.
        self.join(thr=thr, timeout=1.0)

    @classmethod
    def join(cls, thr: Thread, timeout: float = None):
        try:
            thr.join(timeout=timeout)
        except RuntimeError as error:
            print('[ERROR] failed to join thread: %s, timeout: %d' % (error, timeout))
            traceback.print_exc()
