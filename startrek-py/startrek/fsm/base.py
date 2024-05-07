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

import time
import weakref
from abc import ABC, abstractmethod
from enum import IntEnum
from typing import List, Optional

from .machine import S, C, U, T
from .machine import Transition, State, Machine, Delegate


# noinspection PyAbstractClass
class BaseTransition(Transition[C], ABC):
    """ Transition with the index of target state """

    def __init__(self, target: int):
        super().__init__()
        self.__target = target

    @property
    def target(self) -> int:
        """ target state index """
        return self.__target


# noinspection PyAbstractClass
class BaseState(State[C, T], ABC):
    """ State with transitions """

    def __init__(self, index: int):
        super().__init__()
        self.__index = index
        self.__transitions: List[Transition[C]] = []

    @property
    def index(self) -> int:
        return self.__index

    def add_transition(self, transition: Transition[C]):
        assert transition not in self.__transitions, 'transition exists: %s' % transition
        self.__transitions.append(transition)

    # Override
    def evaluate(self, ctx: C, now: float) -> Optional[T]:
        for trans in self.__transitions:
            if trans.evaluate(ctx, now=now):
                # OK, get target state from this transition
                return trans


class MachineStatus(IntEnum):
    """ Machine Status """
    STOPPED = 0
    RUNNING = 1
    PAUSED = 2


class BaseMachine(Machine[C, T, S], ABC):

    def __init__(self):
        super().__init__()
        self.__states: List[S] = []
        self.__current = -1  # current state index
        self.__status = MachineStatus.STOPPED
        self.__delegate_ref: Optional[weakref.ReferenceType] = None

    @property
    def delegate(self) -> Optional[Delegate[C, T, S]]:
        ref = self.__delegate_ref
        if ref is not None:
            return ref()

    @delegate.setter
    def delegate(self, handler: Delegate[C, T, S]):
        self.__delegate_ref = None if handler is None else weakref.ref(handler)

    @property
    @abstractmethod
    def context(self) -> C:
        """ machine itself """
        raise NotImplemented

    #
    #   States
    #
    def add_state(self, state: BaseState[C, T]) -> Optional[S]:
        index = state.index
        assert index >= 0, 'state index error: %d' % index
        count = len(self.__states)
        if index < count:
            # WARNING: return old state that was replaced
            old = self.__states[index]
            self.__states[index] = state
            return old
        # filling empty spaces
        spaces = index - count
        for i in range(spaces):
            self.__states.append(None)
        # append the new state to the tail
        self.__states.append(state)

    def get_state(self, index: int) -> Optional[State[C, T]]:
        return self.__states[index]

    @property  # protected
    def default_state(self) -> State[C, T]:
        return self.__states[0]

    # protected
    def get_target_state(self, transition: BaseTransition[C]) -> State[C, T]:
        # Get target state of this transition
        return self.__states[transition.target]

    @property  # Override
    def current_state(self) -> Optional[State[C, T]]:
        index = self.__current
        if 0 <= index:  # and index < len(self.__states):
            return self.__states[index]

    @current_state.setter  # private
    def current_state(self, state: BaseState[C, T]):
        self.__current = -1 if state is None else state.index

    async def __change_state(self, state: Optional[State[C, T]], now: float):
        """
        Exit current state, and enter new state

        :param state:   next state
        :param now:     current time (seconds from Jan 1, 1970 UTC)
        """
        old = self.current_state
        if old == state:
            # print('[FSM] state not change: %s' % state)
            return False
        machine = self.context
        delegate = self.delegate
        #
        #  Events before state changed
        #
        if delegate is not None:
            # prepare for changing current state to the new one,
            # the delegate can get old state via ctx if need
            await delegate.enter_state(state, machine, now=now)
        if old is not None:
            await old.on_exit(state, machine, now=now)
        #
        #  Change current state
        #
        self.current_state = state
        #
        #  Events after state changed
        #
        if state is not None:
            await state.on_enter(old, machine, now=now)
        if delegate is not None:
            # handle after the current state changed,
            # the delegate can get new state via ctx if need
            await delegate.exit_state(old, machine, now=now)
        return True

    #
    #   Actions
    #

    # Override
    async def start(self):
        now = time.time()
        ok = await self.__change_state(state=self.default_state, now=now)
        assert ok, 'failed to change default state'
        self.__status = MachineStatus.RUNNING

    # Override
    async def stop(self):
        self.__status = MachineStatus.STOPPED
        now = time.time()
        await self.__change_state(state=None, now=now)  # force current state to None

    # Override
    async def pause(self):
        now = time.time()
        machine = self.context
        current = self.current_state
        #
        #  Events before state paused
        #
        if current is not None:
            await current.on_pause(machine, now=now)
        #
        #  Pause state
        #
        self.__status = MachineStatus.PAUSED
        #
        #  Events after state paused
        #
        delegate = self.delegate
        if delegate is not None:
            await delegate.pause_state(current, machine, now=now)

    # Override
    async def resume(self):
        now = time.time()
        machine = self.context
        current = self.current_state
        #
        #  Events before state resumed
        #
        delegate = self.delegate
        if delegate is not None:
            await delegate.resume_state(current, machine, now=now)
        #
        #  Resume state
        #
        self.__status = MachineStatus.RUNNING
        #
        #  Events after state resumed
        #
        if current is not None:
            await current.on_resume(machine, now=now)

    #
    #   Ticker
    #

    # Override
    async def tick(self, now: float, elapsed: float):
        machine = self.context
        current = self.current_state
        if current is not None and self.__status == MachineStatus.RUNNING:
            trans = current.evaluate(machine, now=now)
            if trans is not None:
                # assert isinstance(trans, BaseTransition), 'transition error: %s' % trans
                target = self.get_target_state(transition=trans)
                assert target is not None, 'target state error: %s' % trans.target
                await self.__change_state(state=target, now=now)
