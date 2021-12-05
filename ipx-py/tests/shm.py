
import multiprocessing
import os
from typing import List, Any

from ipx import SharedMemoryCache


g_shared = SharedMemoryCache(size=64, name='ABCDEF')


def test_write(data: List[Any], shm: SharedMemoryCache = None):
    if shm is None:
        shm = SharedMemoryCache(size=64, name='ABCDEF')
    print('======== start writing')
    print('==== shm: %s' % shm)
    for item in data:
        print('==== write: %s' % item)
        shm.append(item)
        print('==== shm: %s' % shm)
    print('======== stop writing')


def test_read(shm: SharedMemoryCache = None):
    if shm is None:
        shm = SharedMemoryCache(size=64, name='ABCDEF')
    print('-------- start reading')
    print('---- shm: %s' % shm)
    data = shm.shift()
    while data is not None:
        print('---- read: %s' % data)
        print('---- shm: %s' % shm)
        data = shm.shift()
    print('-------- stop reading')


def test_process():
    print('******** test multiprocessing...')
    son = multiprocessing.Process(target=test_read)
    son.start()
    test_write(data=['Hello', 'world', 123])


def test_fork():
    print('******** Process (%d) start...' % os.getpid())
    pid = os.fork()
    if pid == 0:
        print('---- Child process %d, parent=%d' % (os.getpid(), os.getppid()))
        test_read(shm=g_shared)
    else:
        print('==== Parent process %d, child=%d' % (os.getpid(), pid))
        test_write(data=['Hello', 'world', 123], shm=g_shared)


if __name__ == '__main__':
    # test_process()
    test_fork()
