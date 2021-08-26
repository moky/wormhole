# -*- coding: utf-8 -*-
#
#   UDP: User Datagram Protocol
#
#                                Written in 2020 by Moky <albert.moky@gmail.com>
#
# ==============================================================================
# MIT License
#
# Copyright (c) 2020 Albert Moky
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

from typing import Optional

from tcp import Channel, BaseConnection

from ..ba import Data
from ..mtp import DataType, TransactionID, Package
from ..mtp import ArrivalHall, Departure, DepartureHall


class PackageConnection(BaseConnection):

    def __init__(self, remote: Optional[tuple], local: Optional[tuple], channel: Optional[Channel]):
        super().__init__(remote=remote, local=local, channel=channel)
        self.__arrival_hall = ArrivalHall()
        self.__departure_hall = DepartureHall()

    # Override
    def tick(self):
        super().tick()
        try:
            self.__process_expired_tasks()
        except IOError as error:
            print('PackageConnection error: %s' % error)

    # Override
    def _process(self):
        delegate = self.delegate
        if delegate is None:
            return
        # receiving
        data, remote = self._receive(max_len=self.MSS)
        if data is None:
            return
        pack = self.__process_income(data=data, remote=remote, destination=self.local_address)
        if pack is None:
            return
        # callback
        delegate.connection_data_received(connection=self, remote=remote, wrapper=pack.head, payload=pack.body)

    def send_command(self, body: bytes, source: Optional[tuple], destination: tuple) -> Departure:
        pack = Package.new(data_type=DataType.COMMAND, body=Data(buffer=body))
        return self.send_package(pack=pack, source=source, destination=destination)

    def send_message(self, body: bytes, source: Optional[tuple], destination: tuple) -> Departure:
        pack = Package.new(data_type=DataType.MESSAGE, body=Data(buffer=body))
        return self.send_package(pack=pack, source=source, destination=destination)

    def send_package(self, pack: Package, source: Optional[tuple], destination: tuple) -> Departure:
        # append as Departure task to waiting queue
        task = self.__departure_hall.append(pack=pack, source=source, destination=destination)
        # send out tasks from waiting queue
        self.__process_expired_tasks()
        return task

    def __process_expired_tasks(self):
        # check departures
        while True:
            outgo = self.__departure_hall.next()
            if outgo is None:
                # all job done
                break
            elif not self.__send_departure(task=outgo):
                # task error
                self.__departure_hall.remove(task=outgo)
        # check & clear expired arrivals
        self.__arrival_hall.purge()

    def __send_departure(self, task: Departure) -> bool:
        # get fragments
        fragments = task.fragments
        if fragments is None or len(fragments) == 0:
            # all fragments respond?
            return False
        # send out all fragments
        for pack in fragments:
            self.send(data=pack.get_bytes(), target=task.destination)
        return True

    def __respond_command(self, sn: TransactionID, body: Data, remote: tuple):
        res = Package.new(data_type=DataType.COMMAND_RESPONSE, sn=sn, body=body)
        self.send(data=res.get_bytes(), target=remote)

    def __respond_message(self, sn: TransactionID, pages: int, index: int, remote: tuple):
        res = Package.new(data_type=DataType.MESSAGE_RESPONSE, sn=sn, pages=pages, index=index, body=OK)
        self.send(data=res.get_bytes(), target=remote)

    def __process_income(self, data: bytes, remote: tuple, destination: tuple) -> Optional[Package]:
        # process income package
        pack = Package.parse(data=Data(buffer=data))
        if pack is None:
            # FIXME: header error? incomplete package?
            return None
        body = pack.body
        if body is None or body.size == 0:
            # should not happen
            return None
        # check data type in package header
        head = pack.head
        data_type = head.data_type
        if data_type.is_command_response:
            # process Command Response:
            #      'PONG'
            #      'OK'
            assert head.index == 0, 'command index error: %d' % head.index
            self.__departure_hall.delete_fragment(sn=head.sn, index=head.index)
            if body == PONG or body == OK:
                # ignore
                return None
            # Unknown Command Response?
            # let the caller to process it
        elif data_type.is_command:
            # process Command:
            #      'PING'
            #      '...'
            if body == PING:
                # PING -> PONG
                self.__respond_command(sn=head.sn, body=PONG, remote=remote)
                return None
            self.__respond_command(sn=head.sn, body=OK, remote=remote)
            # Unknown Command?
            # let the caller to process it
        elif data_type.is_message_response:
            # process Message Response:
            #      'OK'
            #      'AGAIN'
            if body == AGAIN:
                # TODO: reset max_retries?
                return None
            self.__departure_hall.delete_fragment(sn=head.sn, index=head.index)
            if body == OK:
                # ignore
                return None
            # Unknown Message Response?
            # let the caller to process it
        else:
            # process Message/Fragment:
            #      '...'
            self.__respond_message(sn=head.sn, pages=head.pages, index=head.index, remote=remote)
            if data_type.is_fragment:
                # check cached fragments
                pack = self.__arrival_hall.insert(fragment=pack, source=remote, destination=destination)
            # let the caller to process the message
        if body == NOOP:
            # do noting
            return None
        elif body == PING or body == PONG:
            # FIXME: these bodies should be in a Command
            # ignore them
            return None
        else:
            return pack


# Command body
PING = Data(buffer=b'PING')
PONG = Data(buffer=b'PONG')
NOOP = Data(buffer=b'NOOP')
OK = Data(buffer=b'OK')
AGAIN = Data(buffer=b'AGAIN')
