# -*- coding: utf-8 -*-
#
#   IPX: Inter-Process eXchange
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


from .lnc import Notification, NotificationObserver, NotificationCenter

from .mem import Memory, MemoryPool
from .mem import Queue, QueueController
from .mem import CycledBuffer, CycledQueue, GiantQueue

from .shm import SharedMemory, SharedMemoryController
from .shm import DefaultSharedMemoryController

from .arrow import Arrow, SharedMemoryArrow


name = "IPX"

__author__ = 'Albert Moky'

__all__ = [

    # Local Notification
    'Notification', 'NotificationObserver', 'NotificationCenter',

    # Memory Access
    'Memory', 'MemoryPool',
    'Queue', 'QueueController',
    'CycledBuffer', 'CycledQueue', 'GiantQueue',

    # Shared Memory
    'SharedMemory', 'SharedMemoryController',
    'DefaultSharedMemoryController',

    # Half-duplex Pipe
    'Arrow', 'SharedMemoryArrow',
]
