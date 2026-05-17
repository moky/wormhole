# -*- coding: utf-8 -*-
# ==============================================================================
# MIT License
#
# Copyright (c) 2026 Albert Moky
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

"""
    Log Util
    ~~~~~~~~
"""

import logging
import sys

from startrek.utils import Log, LogLevel


MAX_LOG_LEN = 1024


class LimitedFormatter(logging.Formatter):
    """ Limit max log length """

    def __init__(self, fmt: str = None, datefmt: str = None, style: str = '%', max_len: int = None):
        super().__init__(fmt=fmt, datefmt=datefmt, style=style)
        if max_len is None or max_len < 128:
            max_len = MAX_LOG_LEN
        self.__max_len = max_len

    @property
    def max_len(self) -> int:
        return self.__max_len

    # Override
    def format(self, record: logging.LogRecord) -> str:
        text = super().format(record)
        return self._shorten(text=text)

    # private
    def _shorten(self, text: str) -> str:
        max_len = self.max_len
        # assert max_len > 128, 'too short: %s' % max_len
        size = 0 if text is None else len(text)
        if size <= max_len:
            return text
        desc = 'total %d chars' % size
        gaps = len(desc) + 10        # length of middle string: " ... total %d chars ... "
        tail = max_len >> 2          # length of the tail
        pos = max_len - gaps - tail  # length of the head
        return '%s ... %s ... %s' % (text[:pos], desc, text[-tail:])


class ColoredFormatter(LimitedFormatter):
    """ Colored Log """

    _COLORS = {
        logging.DEBUG: '\033[90m',    # grey
        # logging.INFO: '\033[39m',   # foreground
        logging.INFO: None,
        logging.WARNING: '\033[93m',  # yellow
        logging.ERROR: '\033[91m',    # red
    }
    _RESET = '\033[0m'

    def __init__(self, fmt: str = None, datefmt: str = None, style: str = '%', max_len: int = None):
        if datefmt is None:
            datefmt = '%Y-%m-%d %H:%M:%S'
        super().__init__(fmt=fmt, datefmt=datefmt, style=style, max_len=max_len)

    # Override
    def format(self, record: logging.LogRecord) -> str:
        text = super().format(record)
        color = self._COLORS.get(record.levelno)
        if color is None:
            # text without color
            return text
        # colored text
        reset = self._RESET
        return f'{color}{text}{reset}'


class StandardHandler(logging.StreamHandler):
    """ Stream Log Handler """

    def __init__(self, stream=None, level: int = None, fmt: str = None, max_len: int = None):
        if stream is None:
            stream = sys.stdout
        super().__init__(stream=stream)
        #
        #  output level
        #
        if level is None:
            level = LogLevel.DEBUG
        self.setLevel(level=level)
        #
        #  output format
        #
        if fmt is None:
            # fmt = '%(asctime)s | %(levelname)-8s | %(module)s:%(lineno)d > %(message)s'
            fmt = '[%(asctime)s]  %(levelname)-8s | %(message)s\n%(filename)s:%(lineno)d'
        formatter = ColoredFormatter(fmt=fmt, max_len=max_len)
        self.setFormatter(fmt=formatter)

    # Override
    def emit(self, record):
        _fix_record(record=record)
        return super().emit(record=record)


def _fix_record(record: logging.LogRecord):
    """ Fix for caller """
    if hasattr(record, '_fixed'):
        return
    frame = logging.currentframe()
    while frame:
        filename = frame.f_code.co_filename
        frame = frame.f_back
        if filename.endswith('log.py'):
            break
    if frame is not None:
        # record.module = frame.f_globals.get("__name__", "unknown")
        record.filename = frame.f_code.co_filename
        record.lineno = frame.f_lineno
        record._fixed = True


"""
    Initialization
    ~~~~~~~~~~~~~~
"""


def init_log_handlers(logger: logging.Logger, level: int, max_len: int):
    # add stream handler
    handler = StandardHandler(level=level, max_len=max_len)
    logger.addHandler(handler)
    # TODO: add file handler
    logger.setLevel(level=level)


def init_logger(name: str, level: int = LogLevel.DEBUG, max_len: int = MAX_LOG_LEN):
    logger = logging.getLogger(name)
    init_log_handlers(logger=logger, level=level, max_len=max_len)
    Log.logger = logger
