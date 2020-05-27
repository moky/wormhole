#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import random

import sys
import os
import time
from typing import Optional, Union

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

import udp
import dmtp


SERVER_GZ1 = '134.175.87.98'
SERVER_GZ2 = '203.195.224.155'
SERVER_GZ3 = '129.204.94.164'

# SERVER_HOST = '127.0.0.1'
SERVER_HOST = SERVER_GZ1
SERVER_PORT = 9395

CLIENT_HOST = '0.0.0.0'
CLIENT_PORT = random.choice(range(9900, 9999))


class Client(dmtp.Client):

    def __init__(self, hub: udp.Hub):
        super().__init__()
        hub.add_listener(self.peer)
        self.__hub = hub
        self.__locations = {}
        self.source_address = None
        self.server_address = None
        self.identifier = 'moky-%d' % CLIENT_PORT
        self.nat = 'Port Restricted Cone NAT'

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

    def process_message(self, msg: dmtp.Message, source: tuple) -> bool:
        print('received msg from %s:\n\t%s' % (source, msg))
        content = msg.content
        if content is not None:
            print('msg content: "%s"' % content.decode('utf-8'))
        return True

    #
    #   PeerDelegate
    #
    def send_data(self, data: bytes, destination: tuple, source: Union[tuple, int] = None) -> int:
        print('sending data to (%s): %s' % (destination, data))
        self.__hub.send(data=data, destination=destination, source=source)
        return 0


def create_client(local_address: tuple, server_address: tuple):

    # create a hub for sockets
    hub = udp.Hub()
    hub.open(host=local_address[0], port=local_address[1])
    hub.start()

    # create client
    print('UDP client %s -> %s starting ...' % (local_address, server_address))
    client = Client(hub=hub)
    client.server_address = server_address
    return client


def send_text(receiver: str, msg: str):
    location = g_client.get_location(uid=receiver)
    if location is None or location.mapped_address is None:
        print('cannot locate user: %s, %s' % (receiver, location))
        # ask the server to help building a connection
        g_client.call(uid=receiver)
        return False
    mapped_address = location.mapped_address
    address = (mapped_address.ip, mapped_address.port)
    content = msg.encode('utf-8')
    msg = dmtp.Message.new(info={
        'sender': g_client.identifier,
        'receiver': receiver,
        'data': content,
    })
    print('sending msg to %s:\n\t%s' % (address, msg))
    g_client.send_message(msg=msg, destination=address)


if __name__ == '__main__':

    g_client = create_client(local_address=(CLIENT_HOST, CLIENT_PORT),
                             server_address=(SERVER_HOST, SERVER_PORT))

    g_client.identifier = 'hulk'
    friend = 'moky'

    if len(sys.argv) == 3:
        g_client.identifier = sys.argv[1]
        friend = sys.argv[2]

    # login
    g_client.connect(remote_address=g_client.server_address)

    # test send
    text = '你好 %s！' % friend
    while True:
        time.sleep(5)
        print('----')
        send_text(receiver=friend, msg=text)
