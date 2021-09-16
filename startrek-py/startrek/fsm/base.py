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

import weakref
from abc import ABC
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


class BaseState(State[C, T], ABC):
    """ State with transitions """

    def __init__(self):
        super().__init__()
        self.__transitions: List[T] = []

    def add_transition(self, transition: T):
        assert transition not in self.__transitions, 'transition exists'
        self.__transitions.append(transition)

    # Override
    def evaluate(self, ctx: C) -> Optional[T]:
        for trans in self.__transitions:
            if trans.evaluate(ctx):
                # OK, get target state from this transition
                return trans


class BaseMachine(Machine[C, T, S]):

    def __init__(self, default: str):
        super().__init__()
        self.__default = default
        self.__current: Optional[S] = None
        self.__states: Dict[str, S] = {}   # name(str) => State
        self.__delegate: Optional[weakref.ReferenceType] = None
        self.__status: Status = Status.STOPPED

    @property
    def delegate(self) -> Delegate[C, T, S]:
        ref = self.__delegate
        if ref is not None:
            return ref()

    @delegate.setter
    def delegate(self, handler: Delegate[C, T, S]):
        if handler is None:
            self.__delegate = None
        else:
            self.__delegate = weakref.ref(handler)

    @property
    def context(self) -> C:
        raise NotImplemented

    #
    #   States
    #
    def add_state(self, name: str, state: S):
        self.__states[name] = state

    def get_state(self, name: str) -> S:
        return self.__states.get(name)

    @property  # Override
    def default_state(self) -> S:
        return self.__states.get(self.__default)

    @property  # Override
    def current_state(self) -> S:
        return self.__current

    @current_state.setter  # Override
    def current_state(self, state: S):
        self.__current = state

    # Override
    def target_state(self, transition: BaseTransition[C]) -> S:
        return self.__states.get(transition.target)

    # Override
    def change_state(self, state: Optional[S]):
        machine = self.context
        old = self.current_state
        delegate = self.delegate
        # events before state changed
        if delegate is not None:
            delegate.enter_state(state, machine)
        if state is not None:
            state.on_enter(machine)
        # change state
        self.current_state = state
        # events after state changed
        if delegate is not None:
            delegate.exit_state(old, machine)
        if old is not None:
            old.on_exit(machine)

    #
    #   Actions
    #

    # Override
    def start(self):
        self.change_state(state=self.default_state)
        self.__status = Status.RUNNING

    # Override
    def stop(self):
        self.__status = Status.STOPPED
        self.change_state(state=None)

    # Override
    def pause(self):
        machine = self.context
        current = self.current_state
        # events before state paused
        delegate = self.delegate
        if delegate is not None:
            delegate.pause_state(current, machine)
        current.on_pause(machine)
        # pause state
        self.__status = Status.PAUSED

    # Override
    def resume(self):
        machine = self.context
        current = self.current_state
        # reuse state
        self.__status = Status.RUNNING
        # events after state resumed
        delegate = self.delegate
        if delegate is not None:
            delegate.resume_state(current, machine)
        current.on_resume(machine)

    #
    #   Ticker
    #

    # Override
    def tick(self):
        machine = self.context
        current = self.current_state
        if current is not None and self.__status == Status.RUNNING:
            trans = current.evaluate(machine)
            if trans is not None:
                # assert isinstance(trans, BaseTransition), 'transition error: %s' % trans
                target = self.target_state(transition=trans)
                assert target is not None, 'target state error: %s' % trans.target
                self.change_state(state=target)
