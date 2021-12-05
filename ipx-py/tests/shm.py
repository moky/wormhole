
from typing import List, Any

from ipx import SharedMemoryCache


shared = SharedMemoryCache(size=1024)


def test_write(data: List[Any]):
    print('-------- start writing')
    print('shm: %s' % shared.shm[:])
    for item in data:
        print('---- write: %s' % item)
        shared.put(item)
        print('shm: %s' % shared.shm[:])
    print('-------- stop writing')


def test_read():
    print('-------- start reading')
    print('shm: %s' % shared.shm[:])
    data = shared.get()
    while data is not None:
        print('---- read: %s' % data)
        print('shm: %s' % shared.shm[:])
        data = shared.get()
    print('-------- stop reading')


if __name__ == '__main__':
    test_write(data=['Hello', 'world', 123])
    test_read()
