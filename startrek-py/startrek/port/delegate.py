# -*- coding: utf-8 -*-
#
#   Star Trek: Interstellar Transport
#
#                                Written in 2022 by Moky <albert.moky@gmail.com>
#
# ==============================================================================
# MIT License
#
# Copyright (c) 2022 Albert Moky
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

from .ship import Arrival, Departure
from .docker import Docker, DockerStatus


class DockerDelegate(ABC):

    @abstractmethod
    async def docker_received(self, ship: Arrival, docker: Docker):
        """
        Callback when new package received

        :param ship:    income data package container
        :param docker:  connection docker
        """
        raise NotImplemented

    @abstractmethod
    async def docker_sent(self, ship: Departure, docker: Docker):
        """
        Callback when package sent

        :param ship:    outgo data package container
        :param docker:  connection connection
        """
        raise NotImplemented

    @abstractmethod
    async def docker_failed(self, error: OSError, ship: Departure, docker: Docker):
        """
        Callback when failed to send package

        :param error:   error message
        :param ship:    outgo data package container
        :param docker:  connection docker
        """
        raise NotImplemented

    @abstractmethod
    async def docker_error(self, error: OSError, ship: Departure, docker: Docker):
        """
        Callback when connection error

        :param error:   error message
        :param ship:    outgo data package container
        :param docker:  connection docker
        """
        raise NotImplemented

    @abstractmethod
    async def docker_status_changed(self, previous: DockerStatus, current: DockerStatus, docker: Docker):
        """
        Callback when connection status changed

        :param previous: old status
        :param current:  new status
        :param docker:   connection docker
        """
        raise NotImplemented
