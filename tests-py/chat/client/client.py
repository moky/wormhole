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
        self.source_address = None
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

    @staticmethod
    def __analyze_location(location: dmtp.LocationValue) -> int:
        if location is None:
            return -1
        if location.id is None:
            # user ID error
            return -2
        if location.mapped_address is None:
            # address error
            return -3
        if location.signature is None:
            # not signed
            return -4
        # verify addresses and timestamp with signature
        timestamp = dmtp.TimestampValue(value=location.timestamp)
        data = location.mapped_address.data + timestamp.data
        if location.source_address is not None:
            # "source_address" + "mapped_address" + "time"
            data = location.source_address.data + data
        signature = location.signature
        # TODO: verify data and signature with public key
        assert data is not None and signature is not None
        return 0

    def set_location(self, value: dmtp.LocationValue) -> bool:
        if self.__analyze_location(location=value) < 0:
            print('location error: %s' % value)
            return False
        address = value.mapped_address
        self.__locations[value.id] = value
        self.__locations[(address.ip, address.port)] = value
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

    def __sign_location(self, location: dmtp.LocationValue) -> Optional[dmtp.LocationValue]:
        if location is None or location.id is None or location.mapped_address is None:
            # location error
            return None
        # sign ("source-address" + "mapped-address" + "time")
        mapped_address = location.mapped_address
        timestamp = int(time.time())
        data = mapped_address.data + dmtp.TimestampValue(value=timestamp).data
        if self.source_address is None:
            source_address = None
        else:
            source_ip = self.source_address[0]
            source_port = self.source_address[1]
            source_address = dmtp.SourceAddressValue(ip=source_ip, port=source_port)
            data = source_address.data + data
        # TODO: sign it with private key
        s = b'sign(' + data + b')'
        return dmtp.LocationValue.new(uid=location.id, source_address=source_address, mapped_address=mapped_address,
                                      timestamp=timestamp, signature=s, nat=self.nat)

    def sign_in(self, location: dmtp.LocationValue, destination: tuple) -> bool:
        print('server ask signing: %s' % location)
        location = self.__sign_location(location=location)
        if location is None:
            return False
        cmd = dmtp.HelloCommand.new(location=location)
        print('sending cmd: %s' % cmd)
        self.send_command(cmd=cmd, destination=destination)
        self.set_location(value=location)
        return True

    def connect(self, location: dmtp.LocationValue=None, remote_address: tuple=None) -> bool:
        if location is None:
            address = remote_address
        elif location.mapped_address is not None:
            address = (location.mapped_address.ip, location.mapped_address.port)
        elif location.source_address is not None:
            address = (location.source_address.ip, location.source_address.port)
        else:
            return False
        # keep connection alive
        self.__hub.connect(destination=address, source=self.source_address)
        # say hi
        return super().connect(location=location, remote_address=remote_address)

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
        print('received cmd from %s:\n\t%s' % (source, cmd))
        if super().process_command(cmd=cmd, source=source):
            if self.delegate is not None:
                self.delegate.process_command(cmd=cmd, source=source)
            cmd_type = cmd.type
            cmd_value = cmd.value
            if cmd_type == dmtp.From:
                assert isinstance(cmd_value, dmtp.LocationValue), 'call from error: %s' % cmd_value
                mapped_address = cmd_value.mapped_address
                address = (mapped_address.ip, mapped_address.port)
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