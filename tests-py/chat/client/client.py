# -*- coding: utf-8 -*-

import socket
import threading
import time
from abc import abstractmethod
from typing import Optional, Union

import udp
import stun
import dmtp


def time_string(timestamp: int) -> str:
    time_array = time.localtime(timestamp)
    return time.strftime('%y-%m-%d %H:%M:%S', time_array)


"""
    DMTP Client
    ~~~~~~~~~~~
"""


class DMTPPeer(udp.Peer, udp.HubFilter):

    @property
    def filter(self) -> Optional[udp.HubFilter]:
        return self

    #
    #   HubFilter
    #
    def matched(self, data: bytes, source: tuple, destination: tuple) -> bool:
        if len(data) < 12:
            return False
        if data[:3] != b'DIM':
            return False
        return True


class DMTPClientDelegate:

    @abstractmethod
    def process_command(self, cmd: dmtp.Command, source: tuple) -> bool:
        pass

    @abstractmethod
    def process_message(self, msg: dmtp.Message, source: tuple):
        pass


class DMTPClient(dmtp.Client):

    def __init__(self, hub: udp.Hub):
        super().__init__()
        self.__peer: udp.Peer = None
        self.delegate: DMTPClientDelegate = None
        hub.add_listener(self.peer)
        self.__hub = hub
        self.__locations = {}
        self.server_address = None
        self.identifier = 'hulk'
        self.nat = 'Port Restricted Cone NAT'
        # punching threads
        self.__punching = {}

    @property
    def peer(self) -> udp.Peer:
        if self.__peer is None:
            peer = DMTPPeer()
            peer.delegate = self
            peer.start()
            self.__peer = peer
        return self.__peer

    def set_location(self, value: dmtp.LocationValue) -> bool:
        if value.ip is None or value.port == 0:
            print('location error: %s' % value)
            return False
        # TODO: verify mapped-address data with signature
        self.__locations[value.id] = value
        self.__locations[(value.ip, value.port)] = value
        print('location updated: %s' % value)
        return True

    def get_location(self, uid: str = None, source: tuple = None) -> Optional[dmtp.LocationValue]:
        if uid is None:
            return self.__locations.get(source)
        else:
            return self.__locations.get(uid)

    def say_hi(self, destination: tuple) -> bool:
        uid = self.identifier
        location = self.get_location(uid=uid)
        if location is None:
            cmd = dmtp.HelloCommand.new(uid=uid)
        else:
            cmd = dmtp.HelloCommand.new(location=location)
        print('sending cmd: %s' % cmd)
        self.send_command(cmd=cmd, destination=destination)
        return True

    def sign_in(self, value: dmtp.LocationValue, destination: tuple) -> bool:
        uid = value.id
        mapped_ip = value.ip
        mapped_port = value.port
        print('server ask signing: %s' % value)
        if mapped_ip is None or mapped_port == 0:
            return False
        address = dmtp.MappedAddressValue(ip=mapped_ip, port=mapped_port)
        timestamp = int(time.time())
        s_data = address.data + dmtp.TimestampValue(value=timestamp).data
        # TODO: sign mapped-address data
        s = b'sign(' + s_data + b')'
        location = dmtp.LocationValue.new(uid=uid, address=address, timestamp=timestamp, signature=s, nat=self.nat)
        cmd = dmtp.HelloCommand.new(location=location)
        print('sending cmd: %s' % cmd)
        self.send_command(cmd=cmd, destination=destination)
        self.set_location(value=location)
        return True

    def call(self, uid: str) -> bool:
        cmd = dmtp.CallCommand.new(uid=uid)
        print('sending cmd: %s' % cmd)
        self.send_command(cmd=cmd, destination=self.server_address)
        return True

    def ping(self, remote_address: tuple, local_address: tuple=None):
        sock = self.__hub.get_socket(source=local_address)
        if sock is not None:
            res = sock.send(data=b'PING', remote_address=remote_address)
            return res == 4

    def __keep_punching(self, destination: tuple):
        t = self.__punching.get(destination)
        if t is None:
            print('start punching for %s ...' % str(destination))
            t = PunchThread(dmtp_client=self, remote_address=destination)
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
        if super().process_command(cmd=cmd, source=source):
            print('received cmd from %s:\n\t%s' % (source, cmd))
            if self.delegate is not None:
                self.delegate.process_command(cmd=cmd, source=source)
            cmd_type = cmd.type
            cmd_value = cmd.value
            if cmd_type == dmtp.From:
                assert isinstance(cmd_value, dmtp.LocationValue), 'call from error: %s' % cmd_value
                address = (cmd_value.ip, cmd_value.port)
                print('connecting with %s %s' % (cmd_value.id, address))
                self.__hub.connect(destination=address)
                self.__keep_punching(destination=address)
            return True

    def process_message(self, msg: dmtp.Message, source: tuple) -> bool:
        print('received msg from %s:\n\t%s' % (source, msg))
        if self.delegate is not None:
            self.delegate.process_message(msg=msg, source=source)
        return True

    #
    #   PeerDelegate
    #
    def send_data(self, data: bytes, destination: tuple, source: Union[tuple, int] = None) -> int:
        print('sending data to (%s): %s' % (destination, data))
        self.__hub.send(data=data, destination=destination, source=source)
        return 0

    def received_command(self, cmd: bytes, source: tuple, destination: tuple) -> bool:
        self.__stop_punching(destination=source)
        return super().received_command(cmd=cmd, source=source, destination=destination)

    def received_message(self, msg: bytes, source: tuple, destination: tuple) -> bool:
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
        timeout = now + 300
        while self.running and now < timeout:
            when = time_string(now)
            print('[%s] sending "PING" to %s' % (when, remote))
            client.ping(remote_address=remote, local_address=local)
            time.sleep(0.5)
            now = int(time.time())


"""
    STUN Client
    ~~~~~~~~~~~
"""


class STUNClientDelegate:

    @abstractmethod
    def feedback(self, msg: str):
        pass


class STUNClient(stun.Client):

    def __init__(self, hub: udp.Hub):
        super().__init__()
        self.__hub = hub
        self.server_address = None
        self.delegate: STUNClientDelegate = None

    def info(self, msg: str):
        when = time_string(int(time.time()))
        message = '[%s] %s' % (when, msg)
        print(message)
        if self.delegate is not None:
            self.delegate.feedback(msg=message)

    def send(self, data: bytes, destination: tuple, source: Union[tuple, int] = None) -> int:
        try:
            return self.__hub.send(data=data, destination=destination, source=source)
        except socket.error:
            return -1

    def receive(self) -> (bytes, (str, int)):
        try:
            data, source, destination = self.__hub.receive(timeout=2)
            return data, source
        except socket.error:
            return None, None
