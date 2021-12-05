
import multiprocessing
import os
from typing import List, Any

from ipx import SharedMemoryCache


g_shared = SharedMemoryCache(size=64, name='ABCDEF')


def test_write(shared: SharedMemoryCache, data: List[Any]):
    print('======== start writing')
    print('==== shm: %s' % shared)
    for item in data:
        print('==== write: %s' % item)
        shared.put(item)
        print('==== shm: %s' % shared)
    print('======== stop writing')


def test_read(shared: SharedMemoryCache):
    if shared is None:
        shared = g_shared
    print('-------- start reading')
    print('---- shm: %s' % shared)
    data = shared.get()
    while data is not None:
        print('---- read: %s' % data)
        print('---- shm: %s' % shared)
        data = shared.get()
    print('-------- stop reading')


def test_process():
    son = multiprocessing.Process(target=test_read, args=(g_shared,))
    son.start()
    test_write(shared=g_shared, data=['Hello', 'world', 123])


def test_fork():
    print('******** Process (%d) start...' % os.getpid())
    pid = os.fork()
    if pid == 0:
        print('---- Child process %d, parent=%d' % (os.getpid(), os.getppid()))
        test_read(g_shared)
    else:
        print('==== Parent process %d, child=%d' % (os.getpid(), pid))
        test_write(shared=g_shared, data=['Hello', 'world', 123])


if __name__ == '__main__':
    # test_process()
    test_fork()
