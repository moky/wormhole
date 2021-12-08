# -*- coding: utf-8 -*-
#
#   SHM: Shared Memory
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

from abc import ABC, abstractmethod

from ..mem import Memory, MemoryPool
from ..mem import QueueController


class SharedMemory(Memory, ABC):

    @abstractmethod
    def detach(self):
        """ Detaches the shared memory """
        raise NotImplemented

    @abstractmethod
    def destroy(self):
        """ Removes (deletes) the shared memory from the system """
        raise NotImplemented


class SharedMemoryController(QueueController):

    @property
    def shm(self) -> SharedMemory:
        queue = self.queue
        assert isinstance(queue, MemoryPool), 'memory pool error: %s' % queue
        memory = queue.memory
        assert isinstance(memory, SharedMemory), 'shared memory error: %s' % memory
        return memory

    def detach(self):
        """ Detaches the shared memory """
        self.shm.detach()

    def destroy(self):
        """ Removes (deletes) the shared memory from the system """
        self.shm.destroy()
