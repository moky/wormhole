# -*- coding: utf-8 -*-
#
#   Finite State Machine
#
#                                Written in 2021 by Moky <albert.moky@gmail.com>
#
# ==============================================================================
# MIT License
#
# Copyright (c) 2021 Albert Moky
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

from abc import ABC  # , abstractmethod

from .ticker import PrimeMetronome
from .machine import S, C, U, T
from .base import BaseMachine


class AutoMachine(BaseMachine[C, T, S], ABC):

    # @property  # Override
    # @abstractmethod
    # def context(self) -> C:
    #     """ machine itself """
    #     raise NotImplemented

    # Override
    def start(self):
        super().start()
        timer = PrimeMetronome()
        timer.add_ticker(ticker=self)

    # Override
    def stop(self):
        timer = PrimeMetronome()
        timer.remove_ticker(ticker=self)
        super().stop()

    # Override
    def pause(self):
        timer = PrimeMetronome()
        timer.remove_ticker(ticker=self)
        super().pause()

    # Override
    def resume(self):
        super().resume()
        timer = PrimeMetronome()
        timer.add_ticker(ticker=self)
