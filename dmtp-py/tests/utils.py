# -*- coding: utf-8 -*-

import logging
import socket
import sys
from typing import Optional, Iterable

from startrek.types import Log, Logger


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
    Colored Log
    ~~~~~~~~~~~
"""


class ColoredFormatter(logging.Formatter):

    _COLORS = {
        logging.DEBUG: '\033[90m',    # grey
        # logging.INFO: '\033[39m',   # foreground
        logging.INFO: None,
        logging.WARNING: '\033[93m',  # yellow
        logging.ERROR: '\033[91m',    # red
    }
    _RESET = '\033[0m'

    def __init__(self, fmt: str = None, datefmt: str = '%Y-%m-%d %H:%M:%S', style: str = '%'):
        super().__init__(fmt=fmt, datefmt=datefmt, style=style)

    # Override
    def format(self, record: logging.LogRecord) -> str:
        _fix_record(record=record)
        text = super().format(record)
        color = self._COLORS.get(record.levelno)
        if color is not None:
            reset = self._RESET
            return f'{color}{text}{reset}'
        # text without color
        return text


def _fix_record(record: logging.LogRecord):
    """ Fix for caller """
    frame = logging.currentframe()
    while frame:
        filename = frame.f_code.co_filename
        frame = frame.f_back
        if filename.endswith('log.py'):
            break
    if frame is not None:
        record.module = frame.f_globals.get("__name__", "unknown")
        record.lineno = frame.f_lineno


class StandardLogger(Logger):

    def __init__(self, name: str = None, fmt: str = None, level: int = Log.DEBUG):
        super().__init__()
        logger = logging.getLogger(name)
        self.__logger = logger
        if logger.handlers:
            return
        elif fmt is None:
            fmt = '%(asctime)s | %(levelname)-8s | %(module)s:%(lineno)d > %(message)s'
        formatter = ColoredFormatter(fmt=fmt)
        handler = logging.StreamHandler(stream=sys.stdout)
        handler.setFormatter(fmt=formatter)  # output format
        handler.setLevel(level=level)  # output level
        logger.setLevel(level=level)   # output level
        logger.addHandler(handler)

    @property
    def logger(self):
        return self.__logger

    # Override
    def debug(self, msg: str, *args, **kwargs):
        self.logger.debug(msg, *args, **kwargs)

    # Override
    def info(self, msg: str, *args, **kwargs):
        self.logger.info(msg, *args, **kwargs)

    # Override
    def warning(self, msg: str, *args, **kwargs):
        self.logger.warning(msg, *args, **kwargs)

    # Override
    def error(self, msg: str, *args, **kwargs):
        self.logger.error(msg, *args, **kwargs)


Log.logger = StandardLogger(name='UDP')
