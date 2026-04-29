# -*- coding: utf-8 -*-

import socket
import time
from typing import Optional, Iterable


class Log:

    @classmethod
    def info(cls, msg: str):
        now = time.time()
        prefix = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(now))
        print('[%s]         | %s' % (prefix, msg))
        pass

    @classmethod
    def error(cls, msg: str):
        now = time.time()
        prefix = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(now))
        print('[%s]  ERROR  | %s' % (prefix, msg))
        pass


class Inet:

    #
    #   Local SocketAddress
    #

    @classmethod
    def host_name(cls) -> str:
        return socket.gethostname()

    @classmethod
    def addr_info(cls):  # -> List[Tuple[Union[AddressFamily, int], Union[SocketKind, int], int, str, Tuple[Any, ...]]]
        host = socket.gethostname()
        if host is not None:
            try:
                return socket.getaddrinfo(host, None)
            except OSError as error:
                print('[NET] failed to get address info: %s' % error)
                # traceback.print_exc()
                return []

    @classmethod
    def inet_addresses(cls) -> Iterable[str]:
        addresses = set()
        info = cls.addr_info()
        for item in info:
            addresses.add(item[4][0])
        return addresses

    @classmethod
    def inet_address(cls) -> Optional[str]:
        # get from addr info
        info = cls.addr_info()
        for item in info:
            ip = item[4][0]
            if ':' not in ip and '127.0.0.1' != ip:
                return ip
        # get from UDP socket
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            remote = ('8.8.8.8', 8888)
            sock.connect(remote)
            ip = sock.getsockname()[0]
        finally:
            if sock is not None:
                sock.close()
        return ip
