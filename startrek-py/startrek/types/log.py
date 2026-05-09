# -*- coding: utf-8 -*-
#
#   Star Trek: Interstellar Transport
#
#                                Written in 2026 by Moky <albert.moky@gmail.com>
#
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

import logging
from abc import ABC, abstractmethod


class Logger(ABC):
    """ Abstract logging interface """

    @abstractmethod
    def debug(self, msg: str, *args, **kwargs):
        """Log 'msg % args' with severity 'DEBUG'."""
        raise NotImplementedError(
            f'Not implemented: {type(self).__module__}.{type(self).__name__}.debug()'
        )

    @abstractmethod
    def info(self, msg: str, *args, **kwargs):
        """Log 'msg % args' with severity 'INFO'."""
        raise NotImplementedError(
            f'Not implemented: {type(self).__module__}.{type(self).__name__}.info()'
        )

    @abstractmethod
    def warning(self, msg: str, *args, **kwargs):
        """Log 'msg % args' with severity 'WARNING'."""
        raise NotImplementedError(
            f'Not implemented: {type(self).__module__}.{type(self).__name__}.warning()'
        )

    @abstractmethod
    def error(self, msg: str, *args, **kwargs):
        """Log 'msg % args' with severity 'ERROR'."""
        raise NotImplementedError(
            f'Not implemented: {type(self).__module__}.{type(self).__name__}.error()'
        )


class Log:
    """ Global static logger facade """

    # log levels
    DEBUG: int = logging.DEBUG
    INFO: int = logging.INFO
    WARNING: int = logging.WARNING
    ERROR: int = logging.ERROR

    # global logger
    logger: Logger = logging.getLogger('star_trek')

    @classmethod
    def debug(cls, msg: str, *args, **kwargs):
        cls.logger.debug(msg, *args, **kwargs)

    @classmethod
    def info(cls, msg: str, *args, **kwargs):
        cls.logger.info(msg, *args, **kwargs)

    @classmethod
    def warning(cls, msg: str, *args, **kwargs):
        cls.logger.warning(msg, *args, **kwargs)

    @classmethod
    def error(cls, msg: str, *args, **kwargs):
        cls.logger.error(msg, *args, **kwargs)
