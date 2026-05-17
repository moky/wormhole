# -*- coding: utf-8 -*-

import logging
import socket
from typing import Optional, Iterable

from startrek.utils import Log


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
                Log.error('[NET] failed to get address info: %s', error)
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


"""
    STUN Log
    ~~~~~~~~
"""


def _stun_logger(name: str = 'STUN') -> logging.Logger:
    logger = logging.getLogger(name=name)
    if len(logger.handlers) == 0:
        handler = logging.StreamHandler()
        handler.setLevel(level=logging.INFO)
        logger.setLevel(level=logging.INFO)
        logger.addHandler(handler)
    return logger


s_stun_logger = _stun_logger()


def stun_log(msg: str, *args, **kwargs):
    s_stun_logger.info(msg, *args, **kwargs)
