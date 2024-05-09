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

import asyncio
import weakref
from typing import Optional

from .runner import Runnable, Runner


class Daemon:

    def __init__(self, target: Runnable):
        super().__init__()
        self.__target = weakref.ref(target)
        self.__task: Optional[asyncio.Task] = None

    @property  # private
    def target(self) -> Optional[Runnable]:
        ref = self.__target
        if ref is not None:
            return ref()

    def start(self):
        """ Start an async task for running the target """
        target = self.target
        if target is None:
            assert False, 'daemon target lost'
        else:
            assert self.__task is None, 'daemon task is running: %s, %s' % (self.__task, self.target)
        task = Runner.async_run(coroutine=target.run())
        task.add_done_callback(self._done)
        self.__task = task

    def _done(self, t):
        # callback after async task done
        task = self._clean()
        assert task is None or task == t, 'task error: %s, %s' % (t, task)

    def _clean(self) -> Optional[asyncio.Task]:
        # remove async task
        task = self.__task
        self.__task = None
        return task

    def stop(self):
        """ Cancel the async task for running the target """
        task = self._clean()
        if task is None:
            pass
        elif task.done() or task.cancelled():
            pass
        else:
            task.cancel()


# noinspection PyAbstractClass
class DaemonRunner(Runner):
    """
        Daemon Runner
        ~~~~~~~~~~~~~

        @abstract method:
            - process()
    """

    def __init__(self, interval: float):
        super().__init__(interval=interval)
        self.__daemon = Daemon(target=self)

    # Override
    async def start(self):
        # 1. mark this runner to running
        await super().start()
        # 2. start an async task for this runner
        self.__daemon.start()
        # await self.run()

    # Override
    async def stop(self):
        # 1. mark this runner to stopped
        await super().stop()
        # 2. waiting for the runner to stop
        await self.sleep(seconds=self.interval * 2)
        # 3. cancel the async task
        self.__daemon.stop()

    # Override
    async def setup(self):
        # TODO: override to prepare before handling
        pass

    # Override
    async def finish(self):
        # TODO: override to cleanup after handled
        pass
