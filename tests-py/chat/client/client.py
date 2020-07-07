# -*- coding: utf-8 -*-

import threading
import time
from abc import abstractmethod
from typing import Optional

import stun
import dmtp

from .contacts import Session


def time_string(timestamp: int) -> str:
    time_array = time.localtime(timestamp)
    return time.strftime('%y-%m-%d %H:%M:%S', time_array)


"""
    DMTP Client
    ~~~~~~~~~~~
"""


class DMTPClientHandler:

    @abstractmethod
    def process_command(self, cmd: dmtp.Command, source: tuple) -> bool:
        pass

    @abstractmethod
    def process_message(self, msg: dmtp.Message, source: tuple):
        pass


class DMTPClient(dmtp.Client):

    def __init__(self, port: int, host: str='127.0.0.1'):
        super().__init__(local_address=(host, port))
        self.server_address = None
        self.nat = 'Port Restricted Cone NAT'
        self.handler: DMTPClientHandler = None
        self.__identifier = 'moky-%d' % port
        # punching threads
        self.__punching = {}

    @property
    def identifier(self) -> str:
        return self.__identifier

    @identifier.setter
    def identifier(self, value: str):
        self.__identifier = value
        self.delegate.identifier = value

    def connect(self, remote_address: tuple) -> Optional[dmtp.Connection]:
        print('connecting to %s' % str(remote_address))
        conn = self.peer.connect(remote_address=remote_address)
        if conn is not None:
            local_address = self.peer.local_address
            self.__keep_punching(destination=remote_address, source=local_address)
        return conn

    def say_hello(self, destination: tuple) -> bool:
        if super().say_hello(destination=destination):
            return True
        cmd = dmtp.HelloCommand.new(identifier=self.identifier)
        print('send cmd: %s' % cmd)
        self.send_command(cmd=cmd, destination=destination)
        return True

    def call(self, identifier: str) -> bool:
        cmd = dmtp.CallCommand.new(identifier=identifier)
        print('sending cmd: %s' % cmd)
        self.send_command(cmd=cmd, destination=self.server_address)
        return True

    def ping(self, remote_address: tuple, local_address: tuple=None):
        res = self.peer.hub.send(data=b'PING', destination=remote_address, source=local_address)
        return res == 4

    def __keep_punching(self, destination: tuple, source: tuple):
        t = self.__punching.get(destination)
        if t is None:
            print('start punching for %s ...' % str(destination))
            t = PunchThread(dmtp_client=self, remote_address=destination, local_address=source)
            t.start()
            self.__punching[destination] = t

    def __stop_punching(self, destination: tuple):
        t = self.__punching.get(destination)
        if t is not None:
            assert isinstance(t, PunchThread), 'punching thread error: %s' % t
            print('stop punching for %s' % str(destination))
            t.stop()
            self.__punching.pop(destination)

    def process_command(self, cmd: dmtp.Command, source: tuple) -> bool:
        print('received cmd from %s:\n\t%s' % (source, cmd))
        if self.handler is not None:
            self.handler.process_command(cmd=cmd, source=source)
        return super().process_command(cmd=cmd, source=source)

    def process_message(self, msg: dmtp.Message, source: tuple) -> bool:
        print('received msg from %s:\n\t%s' % (source, msg))
        if self.handler is not None:
            self.handler.process_message(msg=msg, source=source)
        # return super().process_message(msg=msg, source=source)
        return True

    def send_command(self, cmd: dmtp.Command, destination: tuple) -> dmtp.Departure:
        print('sending cmd to %s:\n\t%s' % (destination, cmd))
        return super().send_command(cmd=cmd, destination=destination)

    def send_message(self, msg: dmtp.Message, destination: tuple) -> dmtp.Departure:
        print('sending msg to %s:\n\t%s' % (destination, msg))
        return super().send_message(msg=msg, destination=destination)

    def get_sessions(self, identifier: str) -> list:
        """
        Get connected locations for user ID

        :param identifier: user ID
        :return: connected locations and addresses
        """
        assert self.delegate is not None, 'contact delegate not set'
        locations = self.delegate.get_locations(identifier=identifier)
        if len(locations) == 0:
            # locations not found
            return []
        sessions = []
        for loc in locations:
            assert isinstance(loc, dmtp.LocationValue), 'location error: %s' % loc
            if loc.source_address is not None:
                addr = loc.source_address
                if self.peer.is_connected(remote_address=addr):
                    sessions.append(Session(location=loc, address=addr))
                    continue
            if loc.mapped_address is not None:
                addr = loc.mapped_address
                if self.peer.is_connected(remote_address=addr):
                    sessions.append(Session(location=loc, address=addr))
                    continue
        return sessions

    def send_text(self, receiver: str, msg: str) -> Optional[dmtp.Message]:
        sessions = self.get_sessions(identifier=receiver)
        if len(sessions) == 0:
            print('user (%s) not login ...' % receiver)
            # ask the server to help building a connection
            self.call(identifier=receiver)
            return None
        content = msg.encode('utf-8')
        msg = dmtp.Message.new(info={
            'sender': self.identifier,
            'receiver': receiver,
            'time': int(time.time()),
            'data': content,
        })
        for item in sessions:
            assert isinstance(item, Session), 'session error: %s' % item
            print('sending msg to %s:\n\t%s' % (item.address, msg))
            self.send_message(msg=msg, destination=item.address)
        return msg

    #
    #   PeerDelegate
    #
    def received_command(self, cmd: dmtp.Data, source: tuple, destination: tuple) -> bool:
        self.__stop_punching(destination=source)
        return super().received_command(cmd=cmd, source=source, destination=destination)

    def received_message(self, msg: dmtp.Data, source: tuple, destination: tuple) -> bool:
        self.__stop_punching(destination=source)
        return super().received_message(msg=msg, source=source, destination=destination)


class PunchThread(threading.Thread):

    def __init__(self, dmtp_client: DMTPClient, remote_address: tuple, local_address: tuple=None):
        super().__init__()
        self.running = True
        self.__dmtp_client = dmtp_client
        self.__remote_address = remote_address
        self.__local_address = local_address

    def stop(self):
        self.running = False

    def run(self):
        client = self.__dmtp_client
        remote = self.__remote_address
        local = self.__local_address
        now = int(time.time())
        timeout = now + 60
        while self.running and now < timeout:
            when = time_string(now)
            print('[%s] sending "PING" to %s' % (when, remote))
            client.ping(remote_address=remote, local_address=local)
            time.sleep(0.5)
            now = int(time.time())
        # say HI after ping
        client.say_hello(destination=remote)


"""
    STUN Client
    ~~~~~~~~~~~
"""


class STUNClientHandler:

    @abstractmethod
    def feedback(self, msg: str):
        pass


class STUNClient(stun.Client):

    def __init__(self, host: str, port: int):
        super().__init__(host=host, port=port)
        self.server_address = None
        self.handler: STUNClientHandler = None
        # self.retries = 5

    def info(self, msg: str):
        when = time_string(int(time.time()))
        message = '[%s] %s' % (when, msg)
        print(message)
        if self.handler is not None:
            self.handler.feedback(msg=message)
