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

from .machine import Context, Transition, State, Machine, Status, Delegate


class BaseTransition(Transition, ABC):
    """ Transition with the name of target state """

    def __init__(self, target: str):
        super().__init__()
        self.__target = target

    @property
    def target(self) -> str:
        return self.__target


class BaseState(State, ABC):
    """ State with transitions """

    def __init__(self):
        super().__init__()
        self.__transitions: List[Transition] = []

    def add_transition(self, transition: Transition):
        assert transition not in self.__transitions, 'transition exists'
        self.__transitions.append(transition)

    def evaluate(self, ctx: Context) -> Transition:
        for trans in self.__transitions:
            if trans.evaluate(ctx):
                # OK, get target state from this transition
                return trans


class BaseMachine(Machine):

    def __init__(self, default: str):
        super().__init__()
        self.__default = default
        self.__current: Optional[State] = None
        self.__states: Dict[str, State] = {}
        self.__delegate: Optional[weakref.ReferenceType] = None
        self.__status: Status = Status.STOPPED

    @property
    def delegate(self) -> Delegate:
        if self.__delegate is not None:
            return self.__delegate()

    @delegate.setter
    def delegate(self, handler: Delegate):
        if handler is None:
            self.__delegate = None
        else:
            self.__delegate = weakref.ref(handler)

    @property
    def context(self) -> Context:
        raise NotImplemented

    #
    #   States
    #
    def add_state(self, name: str, state: State):
        self.__states[name] = state

    def get_state(self, name: str) -> State:
        return self.__states.get(name)

    @property
    def default_state(self) -> State:
        return self.__states.get(self.__default)

    @property
    def current_state(self) -> State:
        return self.__current

    @current_state.setter
    def current_state(self, state: State):
        self.__current = state

    def target_state(self, transition: BaseTransition) -> State:
        return self.__states.get(transition.target)

    def change_state(self, state: Optional[State]):
        machine = self.context
        current = self.current_state
        delegate = self.delegate
        # events before state changed
        if delegate is not None:
            if current is not None:
                delegate.exit_state(current, machine)
            if state is not None:
                delegate.enter_state(state, machine)
        # change state
        self.current_state = state
        # events after state changed
        if current is not None:
            current.on_exit(machine)
        if state is not None:
            state.on_enter(machine)

    #
    #   Actions
    #
    def start(self):
        self.change_state(state=self.default_state)
        self.__status = Status.RUNNING

    def stop(self):
        self.__status = Status.STOPPED
        self.change_state(state=None)

    def pause(self):
        machine = self.context
        current = self.current_state
        delegate = self.delegate
        if delegate is not None:
            delegate.pause_state(current, machine)
        self.__status = Status.PAUSED
        current.on_pause(machine)

    def resume(self):
        machine = self.context
        current = self.current_state
        delegate = self.delegate
        if delegate is not None:
            delegate.resume_state(current, machine)
        self.__status = Status.RUNNING
        current.on_resume(machine)

    #
    #   Ticker
    #
    def tick(self):
        machine = self.context
        current = self.current_state
        if current is not None and self.__status == Status.RUNNING:
            trans = current.evaluate(machine)
            if isinstance(trans, BaseTransition):
                target = self.target_state(transition=trans)
                assert target is not None, 'target state error: %s' % trans.target
                self.change_state(state=target)
