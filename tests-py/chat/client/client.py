# -*- coding: utf-8 -*-

import time
from abc import abstractmethod
from typing import Optional, Union

import dmtp
import udp


class ClientDelegate:

    @abstractmethod
    def process_command(self, cmd: dmtp.Command, source: tuple) -> bool:
        pass

    @abstractmethod
    def process_message(self, msg: dmtp.Message, source: tuple):
        pass


class Client(dmtp.Client):

    def __init__(self, hub: udp.Hub):
        super().__init__()
        self.delegate: ClientDelegate = None
        hub.add_listener(self.peer)
        self.__hub = hub
        self.__locations = {}
        self.server_address = None
        self.identifier = 'moky'
        self.nat = 'Port Restricted Cone NAT'

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
