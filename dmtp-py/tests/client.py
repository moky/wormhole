#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import random

import sys
import os
import time
from typing import Optional

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
SERVER_PORT = 9394

CLIENT_PORT = random.choice(range(9900, 9999))


class Client(dmtp.Client):

    def __init__(self, hub: udp.Hub):
        super().__init__(hub=hub)
        self.identifier = 'moky-%d' % CLIENT_PORT
        self.nat = 'Port Restricted Cone NAT'
        self.__locations = {}

    def set_location(self, value: dmtp.LocationValue) -> bool:
        if value.ip is None or value.port == 0:
            return False
        self.__locations[value.id] = value
        self.__locations[(value.ip, value.port)] = value
        return True

    def get_location(self, uid: str = None, source: tuple = None) -> Optional[dmtp.LocationValue]:
        if uid is None:
            return self.__locations.get(source)
        else:
            return self.__locations.get(uid)

    def say_hi(self, destination: tuple):
        uid = self.identifier
        location = self.get_location(uid=uid)
        if location is None:
            cmd = dmtp.HelloCommand.new(uid=uid)
        else:
            cmd = dmtp.HelloCommand.new(location=location)
        print('sending cmd: %s' % cmd)
        self.send_command(cmd=cmd, destination=destination)

    def sign_in(self, value: dmtp.LocationValue, destination: tuple) -> bool:
        uid = value.id
        mapped_ip = value.ip
        mapped_port = value.port
        print('server ask sign for ID: %s, %s' % (uid, value.to_dict()))
        if mapped_ip is None or mapped_port == 0:
            return False
        address = dmtp.MappedAddressValue(ip=mapped_ip, port=mapped_port)
        s = b'sign(' + address.data + b')'
        location = dmtp.LocationValue.new(uid=value.id, address=address, signature=s, nat=self.nat)
        self.set_location(value=location)
        cmd = dmtp.HelloCommand.new(location=location)
        print('sending cmd: %s' % cmd)
        self.send_command(cmd=cmd, destination=destination)
        return True

    def __process_from(self, value: dmtp.LocationValue) -> bool:
        print('caller: %s' % value.to_dict())
        if not self.set_location(value=value):
            return False
        self.say_hi(destination=(value.ip, value.port))
        return True

    def process_command(self, cmd: dmtp.Command, source: tuple) -> bool:
        cmd_type = cmd.type
        cmd_value = cmd.value
        if cmd_type == dmtp.From:
            assert isinstance(cmd_value, dmtp.LocationValue), 'call from cmd error: %s' % cmd_value
            return self.__process_from(value=cmd_value)
        else:
            super().process_command(cmd=cmd, source=source)

    def process_message(self, msg: dmtp.Message, source: tuple) -> bool:
        print('received msg from %s:\n\t%s' % (source, msg.to_dict()))
        content = msg.to_dict().get(dmtp.MsgContent)
        if isinstance(content, dmtp.BinaryValue):
            print('msg content: "%s"' % content.data.decode('utf-8'))
        return True


# create a hub for sockets
server_address = (SERVER_HOST, SERVER_PORT)
g_hub = udp.Hub()
g_hub.open(port=CLIENT_PORT)
g_hub.connect(destination=server_address)
g_hub.start()

# create client
g_client = Client(hub=g_hub)


def try_call(uid: str):
    cmd = dmtp.CallCommand.new(uid=uid)
    print('sending cmd: %s' % cmd)
    g_client.send_command(cmd=cmd, destination=server_address)


def send_text(sender: str, receiver: str, msg: str):
    location = g_client.get_location(uid=receiver)
    if location is None or location.ip is None:
        print('cannot locate user: %s, %s' % (receiver, location))
        return False
    address = (location.ip, location.port)
    content = msg.encode('utf-8')
    msg = dmtp.Message.new(info={
        'sender': sender,
        'receiver': receiver,
        'data': content,
    })
    print('sending msg to %s:\n\t%s' % (address, msg.to_dict()))
    g_client.send_message(msg=msg, destination=address)


if __name__ == '__main__':

    g_client.identifier = 'hulk'
    friend = 'moky'

    if len(sys.argv) == 3:
        g_client.identifier = sys.argv[1]
        friend = sys.argv[2]

    # login
    g_client.say_hi(destination=server_address)
    time.sleep(2)

    # test send
    text = '你好 %s！' % friend
    try_call(uid=friend)
    while True:
        time.sleep(5)
        print('----')
        send_text(sender=g_client.identifier, receiver=friend, msg=text)
