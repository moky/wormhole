
import multiprocessing
import os
import time
import traceback
from typing import List, Any

from ipx import Arrow, SharedMemoryArrow


def new_arrow() -> SharedMemoryArrow:
    return SharedMemoryArrow.new(size=64, name='0x00ABCDEF')
    # return SharedMemoryArrow.new(size=64, name=None)


def del_arrow(arrow: SharedMemoryArrow):
    arrow.remove()


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
    # delay
    for i in range(20000):
        time.sleep(0.001)
        if i == 10000:
            arrow.send('aa' + 'b' * 1024 + 'cc')
        else:
            arrow.send(None)
        if i % 1000 == 0:
            print('tick: %d' % i)
        elif i & 0x001F == 0:
            print('.', end=' ')
    arrow.send(b'DONE!')
    print('======== stop writing')


def test_read(arrow: Arrow = None):
    if arrow is None:
        arrow = new_arrow()
    print('-------- start reading')
    print('---- arrow: %s' % arrow)
    for i in range(20000):
        data = arrow.receive()
        while data is not None:
            if isinstance(data, bytes) and len(data) > 64:
                data = data[:30] + b'....' + data[-30:]
            elif isinstance(data, str) and len(data) > 64:
                data = data[:30] + '....' + data[-30:]
            print('---- read %d: %s' % (i, data))
            print('---- arrow %d: %s' % (i, arrow))
            data = arrow.receive()
        time.sleep(0.001)
    print('-------- stop reading')


def test_process():
    print('******** test multiprocessing...')
    child = multiprocessing.Process(target=test_read)
    child.start()
    test_write(data=g_test_data)
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
        test_write(data=g_test_data, arrow=g_shared)
        time.sleep(0.5)
        del_arrow(arrow=g_shared)


g_test_data = [
    'Hello',
    'world',
    123,
    b'AA' + b'B' * 65536 + b'CC'
]


if __name__ == '__main__':
    try:
        # test_process()
        test_fork()
    except Exception as error:
        print('[TEST] error: %s' % error)
        traceback.print_exc()
