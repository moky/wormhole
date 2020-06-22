# -*- coding: utf-8 -*-

import threading
import time
from abc import abstractmethod
from typing import Optional
from weakref import WeakValueDictionary

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


class DMTPPeer(dmtp.Peer, udp.HubFilter):

    @property
    def filter(self) -> Optional[udp.HubFilter]:
        return self

    #
    #   HubFilter
    #
    def check_data(self, data: bytes, source: tuple, destination: tuple) -> bool:
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

    def __init__(self, port: int, host: str='127.0.0.1'):
        super().__init__(host=host, port=port)
        self.delegate: DMTPClientDelegate = None
        self.server_address = None
        self.identifier = 'hulk'
        self.nat = 'Port Restricted Cone NAT'
        # online contacts
        self.__contacts: dict = {}          # ID -> Contact
        self.__map = WeakValueDictionary()  # (IP, port) -> Contact
        # punching threads
        self.__punching = {}

    def _create_peer(self) -> DMTPPeer:
        peer = DMTPPeer()
        peer.delegate = self
        peer.start()
        return peer

    #
    #   Contacts (with locations)
    #

    def get_contact(self, identifier: str=None, address: tuple=None) -> Optional[dmtp.Contact]:
        """ get contact by ID or address """
        if identifier is None:
            assert len(address) == 2, 'address error: %s' % str(address)
            return self.__map.get(address)
        else:
            return self.__contacts.get(identifier)

    def set_location(self, location: dmtp.LocationValue) -> bool:
        """ Login """
        if self.__analyze_location(location=location) < 0:
            print('location error: %s' % location)
            return False
        identifier = location.identifier
        contact = self.get_contact(identifier=identifier)
        if contact is None:
            contact = self._create_contact(identifier=identifier)
        if contact.update_location(location=location):
            self.__contacts[identifier] = contact
            return True

    def remove_location(self, location: dmtp.LocationValue) -> bool:
        """ Logout """
        identifier = location.identifier
        contact = self.get_contact(identifier=identifier)
        if contact is None:
            return False
        assert isinstance(contact, dmtp.Contact), 'contact error: %s' % contact
        if contact.remove_location(location=location):
            if not contact.is_online:
                # all sessions removed/expired
                self.__contacts.pop(identifier, None)
            if location.source_address is not None:
                address = location.source_address
                address = (address.ip, address.port)
                self.__map.pop(address, None)
            if location.mapped_address is not None:
                address = location.mapped_address
                address = (address.ip, address.port)
                self.__map.pop(address, None)
            return True

    def update_address(self, address: tuple, contact: dmtp.Contact) -> bool:
        if contact.update_address(address=address):
            self.__map[address] = contact
            return True

    # noinspection PyMethodMayBeStatic
    def __analyze_location(self, location: dmtp.LocationValue) -> int:
        if location is None:
            return -1
        if location.identifier is None:
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

    def __sign_location(self, location: dmtp.LocationValue) -> Optional[dmtp.LocationValue]:
        if location is None or location.identifier is None or location.mapped_address is None:
            # location error
            return None
        # data = "source_address" + "mapped_address" + "relayed_address" + "time"
        mapped_address = location.mapped_address
        data = mapped_address.data
        # source address
        source_ip = self.local_address[0]
        source_port = self.local_address[1]
        source_address = dmtp.SourceAddressValue(ip=source_ip, port=source_port)
        data = source_address.data + data
        # relayed address
        if location.relayed_address is None:
            relayed_address = None
        else:
            relayed_address = location.relayed_address
            data = data + relayed_address.data
        # time
        timestamp = int(time.time())
        data += dmtp.TimestampValue(value=timestamp).data
        # TODO: sign it with private key
        signature = b'sign(' + data + b')'
        return dmtp.LocationValue.new(identifier=location.identifier,
                                      source_address=source_address,
                                      mapped_address=mapped_address,
                                      relayed_address=relayed_address,
                                      timestamp=timestamp, signature=signature, nat=self.nat)

    def say_hi(self, destination: tuple) -> bool:
        sender = self.get_contact(identifier=self.identifier)
        if sender is None:
            location = None
        else:
            location = sender.get_location(address=self.local_address)
        if location is None:
            cmd = dmtp.HelloCommand.new(identifier=self.identifier)
        else:
            cmd = dmtp.HelloCommand.new(location=location)
        print('sending cmd: %s' % cmd)
        self.send_command(cmd=cmd, destination=destination)
        return True

    def sign_in(self, location: dmtp.LocationValue, destination: tuple) -> bool:
        print('server ask signing: %s' % location)
        location = self.__sign_location(location=location)
        if location is None:
            return False
        cmd = dmtp.HelloCommand.new(location=location)
        print('sending cmd: %s' % cmd)
        self.send_command(cmd=cmd, destination=destination)
        self.set_location(location=location)
        return True

    def connect(self, remote_address: tuple) -> bool:
        print('connecting to %s' % str(remote_address))
        if super().connect(remote_address=remote_address):
            self.__keep_punching(destination=remote_address, source=self.local_address)
            return True

    def call(self, identifier: str) -> bool:
        cmd = dmtp.CallCommand.new(identifier=identifier)
        print('sending cmd: %s' % cmd)
        self.send_command(cmd=cmd, destination=self.server_address)
        return True

    def ping(self, remote_address: tuple, local_address: tuple=None):
        res = self.hub.send(data=b'PING', destination=remote_address, source=local_address)
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
        if super().process_command(cmd=cmd, source=source):
            if self.delegate is not None:
                self.delegate.process_command(cmd=cmd, source=source)
            return True

    def process_message(self, msg: dmtp.Message, source: tuple) -> bool:
        print('received msg from %s:\n\t%s' % (source, msg))
        if self.delegate is not None:
            self.delegate.process_message(msg=msg, source=source)
        return True

    #
    #   PeerDelegate
    #
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
        timeout = now + 60
        while self.running and now < timeout:
            when = time_string(now)
            print('[%s] sending "PING" to %s' % (when, remote))
            client.ping(remote_address=remote, local_address=local)
            time.sleep(0.5)
            now = int(time.time())
        # say HI after ping
        client.say_hi(destination=remote)


"""
    STUN Client
    ~~~~~~~~~~~
"""


class STUNClientDelegate:

    @abstractmethod
    def feedback(self, msg: str):
        pass


class STUNClient(stun.Client):

    def __init__(self, host: str, port: int):
        super().__init__(host=host, port=port)
        self.server_address = None
        self.delegate: STUNClientDelegate = None
        # self.retries = 5

    def info(self, msg: str):
        when = time_string(int(time.time()))
        message = '[%s] %s' % (when, msg)
        print(message)
        if self.delegate is not None:
            self.delegate.feedback(msg=message)
