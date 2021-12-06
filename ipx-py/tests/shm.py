
import multiprocessing
import os
import time
import traceback
from typing import List, Any

from ipx import Arrow, SharedMemoryArrow


def new_arrow() -> SharedMemoryArrow:
    return SharedMemoryArrow.new(size=64, name='ABCDEF')
    # return SharedMemoryArrow.new(size=64, name='')


def del_arrow(arrow: SharedMemoryArrow):
    # arrow.remove()
    pass


g_shared = new_arrow()


def test_write(data: List[Any], arrow: Arrow = None):
    if arrow is None:
        arrow = new_arrow()
    print('======== start writing')
    print('==== arrow: %s' % arrow)
    for item in data:
        print('==== write: %s' % item)
        arrow.send(item)
        print('==== arrow: %s' % arrow)
    print('======== stop writing')


def test_read(arrow: Arrow = None):
    if arrow is None:
        arrow = new_arrow()
    print('-------- start reading')
    print('---- arrow: %s' % arrow)
    data = arrow.receive()
    while data is not None:
        print('---- read: %s' % data)
        print('---- arrow: %s' % arrow)
        data = arrow.receive()
    print('-------- stop reading')


def test_process():
    print('******** test multiprocessing...')
    child = multiprocessing.Process(target=test_read)
    child.start()
    test_write(data=['Hello', 'world', 123])
    child.join()
    # g_shared.remove()


def test_fork():
    print('******** Process (%d) start...' % os.getpid())
    pid = os.fork()
    if pid == 0:
        print('---- Child process %d, parent=%d' % (os.getpid(), os.getppid()))
        test_read(arrow=g_shared)
    else:
        print('==== Parent process %d, child=%d' % (os.getpid(), pid))
        test_write(data=['Hello', 'world', 123], arrow=g_shared)
        time.sleep(0.5)
        del_arrow(arrow=g_shared)


if __name__ == '__main__':
    try:
        test_process()
        # test_fork()
    except Exception as error:
        print('[TEST] error: %s' % error)
        traceback.print_exc()
