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

from abc import ABC
from typing import Optional

from tcp import Channel, ActiveConnection, BaseHub

from ..ba import Data
from ..mtp import DataType, TransactionID, Package
from ..mtp import ArrivalHall, Departure, DepartureHall


class PackageConnection(ActiveConnection, ABC):

    """
        Maximum Segment Size
        ~~~~~~~~~~~~~~~~~~~~
        Buffer size for receiving package

        MTU        : 1500 bytes (excludes 14 bytes ethernet header & 4 bytes FCS)
        IP header  :   20 bytes
        TCP header :   20 bytes
        UDP header :    8 bytes
    """
    MSS = 1472  # 1500 - 20 - 8

    def __init__(self, remote: tuple, local: tuple, channel: Optional[Channel] = None):
        super().__init__(remote=remote, local=local, channel=channel)
        self.__arrival_hall = ArrivalHall()
        self.__departure_hall = DepartureHall()

    def tick(self):
        super().tick()
        self.__process_expired_tasks()

    def send_package(self, pack: Package, source: tuple, destination: tuple):
        # append as Departure task to waiting queue
        self.__departure_hall.append(pack=pack, source=source, destination=destination)
        # send out tasks from waiting queue
        self.__process_expired_tasks()

    def __process_expired_tasks(self):
        # check departures
        while True:
            outgo = self.__departure_hall.next()
            if outgo is None:
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
        res = Package.new(data_type=DataType.CommandResponse, sn=sn, body=body)
        self.send(data=res.get_bytes(), target=remote)

    def __respond_message(self, sn: TransactionID, pages: int, offset: int, remote: tuple):
        res = Package.new(data_type=DataType.MessageResponse, sn=sn, pages=pages, offset=offset, body=OK)
        self.send(data=res.get_bytes(), target=remote)

    def receive_package(self, source: tuple, destination: tuple) -> Optional[Package]:
        """
        Receive data package from remote address

        :param source:      remote address
        :param destination: local address
        :return: complete package
        """
        while True:
            data, remote = self.receive(max_len=self.MSS)
            if data is None:  # or remote is None:
                # received nothing
                return None
            assert remote == source, 'source address error: %s, %s' % (source, remote)
            pack = self.__process_income(data=data, remote=remote, destination=destination)
            if pack is not None:
                # received a complete package
                return pack

    def __process_income(self, data: bytes, remote: tuple, destination: tuple) -> Optional[Package]:
        # process income package
        pack = Package.parse(data=Data(data=data))
        if pack is None:
            return None
        body = pack.body
        if body is None or body.size == 0:
            # should not happen
            return None
        # check data type in package header
        head = pack.head
        data_type = head.data_type
        if data_type.is_command_response:
            # process CommandResponse:
            #      'PONG'
            #      'OK'
            assert head.offset == 0, 'command offset error: %d' % head.offset
            self.__departure_hall.delete_fragment(sn=head.sn, offset=head.sn)
            if body == PONG:
                # ignore
                return None
            elif body == OK:
                # ignore
                return None
            # Unknown Command Response?
            # let the caller to process it
        elif data_type.is_command:
            # process Command:
            #      'PING'
            #      'NOOP'
            if body == PING:
                # PING -> PONG
                self.__respond_command(sn=head.sn, body=PONG, remote=remote)
            elif body == NOOP:
                # NOOP -> OK
                self.__respond_command(sn=head.sn, body=OK, remote=remote)
            # Unknown Command?
            # let the caller to process it
        elif data_type.is_message_response:
            # process MessageResponse:
            #      'OK'
            #      'AGAIN'
            if body == AGAIN:
                # TODO: reset max_retries?
                return None
            self.__departure_hall.delete_fragment(sn=head.sn, offset=head.offset)
            if body == PONG:
                # this body should be in a Command
                return None
            elif body == OK:
                # ignore
                return None
            # Unknown MessageResponse?
            # let the caller to process it
        elif data_type.is_message_fragment:
            # process MessageFragment:
            #      'OK'
            #      'AGAIN'
            self.__respond_message(sn=head.sn, pages=head.pages, offset=head.offset, remote=remote)
            # check cached fragments
            pack = self.__arrival_hall.insert(fragment=pack, source=remote, destination=destination)
        else:
            # process Message:
            #      '...'
            assert data_type.is_message, 'data type error: %s' % data_type
            if body == PING or body == PONG or body == NOOP or body == OK:
                # these bodies should be in an Command
                # ignore them
                return None
            self.__respond_message(sn=head.sn, pages=1, offset=0, remote=remote)
        # OK
        return pack

    def heartbeat(self, destination: tuple):
        """ Send a heartbeat package to remote address """
        pack = Package.new(data_type=DataType.Command, body=PING)
        self.send(data=pack.get_bytes(), target=destination)


# Command body
PING = Data(data=b'PING')
PONG = Data(data=b'PONG')
NOOP = Data(data=b'NOOP')
OK = Data(data=b'OK')
AGAIN = Data(data=b'AGAIN')


class PackageHub(BaseHub, ABC):

    def get_package_connection(self, remote: tuple, local: tuple) -> Optional[PackageConnection]:
        conn = self.connect(remote=remote, local=local)
        if isinstance(conn, PackageConnection):
            return conn

    def receive_package(self, source: tuple, destination: tuple) -> Optional[Package]:
        conn = self.get_package_connection(remote=source, local=destination)
        if conn is None:
            return None
        try:
            return conn.receive_package(source=source, destination=destination)
        except IOError as error:
            print('PackageHub error: %s' % error)

    def send_package(self, pack: Package, source: tuple, destination: tuple) -> bool:
        conn = self.get_package_connection(remote=source, local=destination)
        if conn is None:
            return False
        try:
            conn.send_package(pack=pack, source=source, destination=destination)
            return True
        except IOError as error:
            print('PackageHub error: %s' % error)
