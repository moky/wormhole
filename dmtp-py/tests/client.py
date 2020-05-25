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
        self.server_address = None
        self.identifier = 'moky-%d' % CLIENT_PORT
        self.nat = 'Port Restricted Cone NAT'

    def set_location(self, value: dmtp.LocationValue) -> bool:
        if value.mapped_address is None:
            print('location error: %s' % value)
            return False
        # TODO: verify mapped-address data with signature
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

    def sign_in(self, value: dmtp.LocationValue, destination: tuple) -> bool:
        uid = value.id
        print('server ask signing: %s' % value)
        if value.mapped_address is None:
            return False
        mapped_address = value.mapped_address
        timestamp = int(time.time())
        # TODO: sign ("source-address" + "mapped-address" + "time")
        v_time = dmtp.TimestampValue(value=timestamp)
        s_data = mapped_address.data + v_time.data
        s = b'sign(' + s_data + b')'
        # create location value
        location = dmtp.LocationValue.new(uid=uid, mapped_address=mapped_address,
                                          timestamp=timestamp, signature=s, nat=self.nat)
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
    g_client.say_hi(destination=g_client.server_address)

    # test send
    text = '你好 %s！' % friend
    while True:
        time.sleep(5)
        print('----')
        send_text(receiver=friend, msg=text)
