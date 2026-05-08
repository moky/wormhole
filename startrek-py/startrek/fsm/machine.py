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
from typing import Optional, TypeVar, Generic

from ..types import Timestamp
from ..skywalker import Ticker

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
    def evaluate(self, ctx: C, now: Timestamp) -> bool:
        """
        Evaluate the current state

        :param ctx:     context (machine)
        :param now:     current time (seconds from Jan 1, 1970 UTC)
        :return True when current state should be changed
        """
        raise NotImplementedError(
            f'Not implemented: {type(self).__module__}.{type(self).__name__}.evaluate()'
        )


class State(ABC, Generic[C, T]):
    """ Finite State """

    @abstractmethod
    def evaluate(self, ctx: C, now: Timestamp) -> Optional[T]:
        """
        Called by machine.tick() to evaluate each transitions

        :param ctx:     context (machine)
        :param now:     current time (seconds from Jan 1, 1970 UTC)
        :return success transition, or None to stay the current state
        """
        raise NotImplementedError(
            f'Not implemented: {type(self).__module__}.{type(self).__name__}.evaluate()'
        )

    @abstractmethod
    async def on_enter(self, old, ctx: C, now: Timestamp):
        """
        Called after new state entered

        :param old:     previous state
        :param ctx:     context (machine)
        :param now:     current time (seconds from Jan 1, 1970 UTC)
        """
        raise NotImplementedError(
            f'Not implemented: {type(self).__module__}.{type(self).__name__}.on_enter()'
        )

    @abstractmethod
    async def on_exit(self, new, ctx: C, now: Timestamp):
        """
        Called before old state exited

        :param new:     next state
        :param ctx:     context (machine)
        :param now:     current time (seconds from Jan 1, 1970 UTC)
        """
        raise NotImplementedError(
            f'Not implemented: {type(self).__module__}.{type(self).__name__}.on_exit()'
        )

    @abstractmethod
    async def on_pause(self, ctx: C, now: Timestamp):
        """
        Called before current state paused

        :param ctx:     context (machine)
        :param now:     current time (seconds from Jan 1, 1970 UTC)
        """
        raise NotImplementedError(
            f'Not implemented: {type(self).__module__}.{type(self).__name__}.on_pause()'
        )

    @abstractmethod
    async def on_resume(self, ctx: C, now: Timestamp):
        """
        Called after current state resumed

        :param ctx:     context (machine)
        :param now:     current time (seconds from Jan 1, 1970 UTC)
        """
        raise NotImplementedError(
            f'Not implemented: {type(self).__module__}.{type(self).__name__}.on_resume()'
        )


class Delegate(ABC, Generic[C, T, S]):
    """ State Machine Delegate """

    @abstractmethod
    async def enter_state(self, state: Optional[S], ctx: C, now: Timestamp):
        """
        Called before enter new state
        (get current state from context)

        :param state:   new state
        :param ctx:     context (machine)
        :param now:     current time (seconds from Jan 1, 1970 UTC)
        """
        raise NotImplementedError(
            f'Not implemented: {type(self).__module__}.{type(self).__name__}.enter_state()'
        )

    @abstractmethod
    async def exit_state(self, state: Optional[S], ctx: C, now: Timestamp):
        """
        Called after exit old state
        (get current state from context)

        :param state:   old state
        :param ctx:     context (machine)
        :param now:     current time (seconds from Jan 1, 1970 UTC)
        """
        raise NotImplementedError(
            f'Not implemented: {type(self).__module__}.{type(self).__name__}.exit_state()'
        )

    @abstractmethod
    async def pause_state(self, state: Optional[S], ctx: C, now: Timestamp):
        """
        Called after pause this state

        :param state:   current state
        :param ctx:     context (machine)
        :param now:     current time (seconds from Jan 1, 1970 UTC)
        """
        raise NotImplementedError(
            f'Not implemented: {type(self).__module__}.{type(self).__name__}.pause_state()'
        )

    @abstractmethod
    async def resume_state(self, state: Optional[S], ctx: C, now: Timestamp):
        """
        Called before resume this state

        :param state:   current state
        :param ctx:     context (machine)
        :param now:     current time (seconds from Jan 1, 1970 UTC)
        """
        raise NotImplementedError(
            f'Not implemented: {type(self).__module__}.{type(self).__name__}.resume_state()'
        )


class Machine(Ticker, ABC, Generic[C, T, S]):
    """ State Machine """

    @property
    @abstractmethod
    def current_state(self) -> Optional[S]:
        raise NotImplementedError(
            f'Not implemented: {type(self).__module__}.{type(self).__name__}.current_state getter'
        )

    @abstractmethod
    async def start(self) -> bool:
        """ Change current state to 'default' """
        raise NotImplementedError(
            f'Not implemented: {type(self).__module__}.{type(self).__name__}.start()'
        )

    @abstractmethod
    async def stop(self) -> bool:
        """ Change current state to null """
        raise NotImplementedError(
            f'Not implemented: {type(self).__module__}.{type(self).__name__}.stop()'
        )

    @abstractmethod
    async def pause(self) -> bool:
        """ Pause machine, current state not change """
        raise NotImplementedError(
            f'Not implemented: {type(self).__module__}.{type(self).__name__}.pause()'
        )

    @abstractmethod
    async def resume(self) -> bool:
        """ Resume machine with current state """
        raise NotImplementedError(
            f'Not implemented: {type(self).__module__}.{type(self).__name__}.resume()'
        )
