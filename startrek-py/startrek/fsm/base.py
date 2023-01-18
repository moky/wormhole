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
from typing import List, Optional, Dict

from .machine import S, C, U, T
from .machine import Transition, State, Machine, Status, Delegate


class BaseTransition(Transition[C], ABC):
    """ Transition with the name of target state """

    def __init__(self, target: str):
        super().__init__()
        self.__target = target

    @property
    def target(self) -> str:
        """ target state name """
        return self.__target

    # @abstractmethod  # Override
    # def evaluate(self, ctx: C, now: float) -> bool:
    #     raise NotImplemented


class BaseState(State[C, T], ABC):
    """ State with transitions """

    def __init__(self):
        super().__init__()
        self.__transitions: List[Transition[C]] = []

    def add_transition(self, transition: Transition[C]):
        assert transition not in self.__transitions, 'transition exists: %s' % transition
        self.__transitions.append(transition)

    # Override
    def evaluate(self, ctx: C, now: float) -> Optional[T]:
        for trans in self.__transitions:
            if trans.evaluate(ctx, now=now):
                # OK, get target state from this transition
                return trans

    # @abstractmethod  # Override
    # def on_enter(self, old, ctx: C, now: float):
    #     raise NotImplemented
    #
    # @abstractmethod  # Override
    # def on_exit(self, new, ctx: C, now: float):
    #     raise NotImplemented
    #
    # @abstractmethod  # Override
    # def on_pause(self, ctx: C):
    #     raise NotImplemented
    #
    # @abstractmethod  # Override
    # def on_resume(self, ctx: C):
    #     raise NotImplemented


class BaseMachine(Machine[C, T, S], ABC):

    def __init__(self, default: str):
        super().__init__()
        self.__default = default           # default state name
        self.__current = None              # ref(current_state)
        self.__states: Dict[str, S] = {}   # str(name) => State
        self.__delegate: Optional[weakref.ReferenceType] = None
        self.__status: Status = Status.STOPPED

    @property
    def delegate(self) -> Delegate[C, T, S]:
        ref = self.__delegate
        if ref is not None:
            return ref()

    @delegate.setter
    def delegate(self, handler: Delegate[C, T, S]):
        self.__delegate = None if handler is None else weakref.ref(handler)

    @property
    @abstractmethod
    def context(self) -> C:
        """ machine itself """
        raise NotImplemented

    #
    #   States
    #
    def set_state(self, name: str, state: State[C, T]):
        self.__states[name] = state

    def get_state(self, name: str) -> Optional[State[C, T]]:
        return self.__states.get(name)

    @property  # protected
    def default_state(self) -> State[C, T]:
        return self.__states.get(self.__default)

    # protected
    def get_target_state(self, transition: BaseTransition[C]) -> State[C, T]:
        # Get target state of this transition
        return self.__states.get(transition.target)

    @property  # Override
    def current_state(self) -> Optional[State[C, T]]:
        ref = self.__current
        if ref is not None:
            return ref()

    def __set_current_state(self, state: State[C, T]):
        self.__current = None if state is None else weakref.ref(state)

    def __change_state(self, state: Optional[State[C, T]], now: float):
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
            delegate.enter_state(state, machine)
        if old is not None:
            old.on_exit(state, machine, now=now)
        #
        #  Change current state
        #
        self.__set_current_state(state=state)
        #
        #  Events after state changed
        #
        if state is not None:
            state.on_enter(old, machine, now=now)
        if delegate is not None:
            # handle after the current state changed,
            # the delegate can get new state via ctx if need
            delegate.exit_state(old, machine)
        return True

    #
    #   Actions
    #

    # Override
    def start(self):
        now = time.time()
        ok = self.__change_state(state=self.default_state, now=now)
        assert ok, 'failed to change default state'
        self.__status = Status.RUNNING

    # Override
    def stop(self):
        self.__status = Status.STOPPED
        now = time.time()
        self.__change_state(state=None, now=now)  # force current state to None

    # Override
    def pause(self):
        machine = self.context
        current = self.current_state
        #
        #  Events before state paused
        #
        if current is not None:
            current.on_pause(machine)
        #
        #  Pause state
        #
        self.__status = Status.PAUSED
        #
        #  Events after state paused
        #
        delegate = self.delegate
        if delegate is not None:
            delegate.pause_state(current, machine)

    # Override
    def resume(self):
        machine = self.context
        current = self.current_state
        #
        #  Events before state resumed
        delegate = self.delegate
        if delegate is not None:
            delegate.resume_state(current, machine)
        #
        #  Resume state
        #
        self.__status = Status.RUNNING
        #
        #  Events after state resumed
        #
        if current is not None:
            current.on_resume(machine)

    #
    #   Ticker
    #

    # Override
    def tick(self, now: float, elapsed: float):
        machine = self.context
        current = self.current_state
        if current is not None and self.__status == Status.RUNNING:
            trans = current.evaluate(machine, now=now)
            if trans is not None:
                # assert isinstance(trans, BaseTransition), 'transition error: %s' % trans
                target = self.get_target_state(transition=trans)
                assert target is not None, 'target state error: %s' % trans.target
                self.__change_state(state=target, now=now)
