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

from abc import ABC, abstractmethod
from enum import IntEnum
from typing import Optional, TypeVar, Generic

from .ticker import Ticker

S = TypeVar('S')  # State
C = TypeVar('C')  # Context
U = TypeVar('U')
T = TypeVar('T')  # Transition


class Context(ABC):
    """ State Machine Context """
    pass


class Transition(ABC, Generic[C]):
    """ State Transition """

    @abstractmethod
    def evaluate(self, ctx: C, now: float) -> bool:
        """
        Evaluate the current state

        :param ctx:     context (machine)
        :param now:     current time (seconds from Jan 1, 1970 UTC)
        :return True when current state should be changed
        """
        raise NotImplemented


class State(ABC, Generic[C, T]):
    """ Finite State """

    @abstractmethod
    def on_enter(self, old, ctx: C, now: float):
        """
        Called after new state entered

        :param old:     previous state
        :param ctx:     context (machine)
        :param now:     current time (seconds from Jan 1, 1970 UTC)
        """
        raise NotImplemented

    @abstractmethod
    def on_exit(self, new, ctx: C, now: float):
        """
        Called before old state exited

        :param new:     next state
        :param ctx:     context (machine)
        :param now:     current time (seconds from Jan 1, 1970 UTC)
        """
        raise NotImplemented

    @abstractmethod
    def on_pause(self, ctx: C):
        """
        Called before current state paused

        :param ctx: context (machine)
        """
        raise NotImplemented

    @abstractmethod
    def on_resume(self, ctx: C):
        """
        Called after current state resumed

        :param ctx: context (machine)
        """
        raise NotImplemented

    @abstractmethod
    def evaluate(self, ctx: C, now: float) -> Optional[T]:
        """
        Called by machine.tick() to evaluate each transitions

        :param ctx:     context (machine)
        :param now:     current time (seconds from Jan 1, 1970 UTC)
        :return success transition, or None to stay the current state
        """
        raise NotImplemented


class Delegate(ABC, Generic[C, T, S]):
    """ State Machine Delegate """

    @abstractmethod
    def enter_state(self, state: S, ctx: C):
        """
        Called before enter new state
        (get current state from context)

        :param state: new state
        :param ctx:   context (machine)
        """
        raise NotImplemented

    @abstractmethod
    def exit_state(self, state: S, ctx: C):
        """
        Called after exit old state
        (get current state from context)

        :param state: old state
        :param ctx:   context (machine)
        """
        raise NotImplemented

    @abstractmethod
    def pause_state(self, state: S, ctx: C):
        """
        Called after pause this state

        :param state: current state
        :param ctx:   context (machine)
        """
        raise NotImplemented

    @abstractmethod
    def resume_state(self, state: S, ctx: C):
        """
        Called before resume this state

        :param state: current state
        :param ctx:   context (machine)
        """
        raise NotImplemented


class Machine(Ticker, ABC, Generic[C, T, S]):
    """ State Machine """

    @property
    @abstractmethod
    def current_state(self) -> S:
        raise NotImplemented

    @abstractmethod
    def start(self):
        """ Change current state to 'default' """
        raise NotImplemented

    @abstractmethod
    def stop(self):
        """ Change current state to null """
        raise NotImplemented

    @abstractmethod
    def pause(self):
        """ Pause machine, current state not change """
        raise NotImplemented

    @abstractmethod
    def resume(self):
        """ Resume machine with current state """
        raise NotImplemented


class Status(IntEnum):
    """ Machine Status """
    STOPPED = 0
    RUNNING = 1
    PAUSED = 2
