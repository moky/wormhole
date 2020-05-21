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


SERVER_HOST = '127.0.0.1'
SERVER_PORT = 9394

CLIENT_PORT = random.choice(range(9900, 9999))


class Client(dmtp.Client):

    def __init__(self, hub: udp.Hub):
        super().__init__(hub=hub)
        self.identifier = 'moky-%d' % CLIENT_PORT
        self.nat = 'Port Restricted Cone NAT'
        self.__locations = {}

    def location(self, uid: str = None, source: tuple = None) -> Optional[dmtp.LocationValue]:
        print('getting location: %s, %s' % (uid, source))
        if uid is None:
            return self.__locations.get(source)
        else:
            return self.__locations.get(uid)

    def say_hi(self, destination: tuple):
        f_id = dmtp.Field(t=dmtp.ID, v=dmtp.StringValue(string=self.identifier))
        cmd = dmtp.Command(t=dmtp.Login, v=f_id)
        print('sending cmd: %s' % cmd)
        self.send_command(cmd=cmd, destination=server_address)

    def sign_in(self, value: dmtp.LocationValue, destination: tuple) -> bool:
        uid = value.id
        mapped_ip = value.ip
        mapped_port = value.port
        print('server ask sign for ID: %s, %s' % (uid, value.to_dict()))
        s = b'BASE64(signature)'
        loc = dmtp.LocationValue.new(uid=value.id, ip=mapped_ip, port=mapped_port, signature=s, nat=self.nat)
        cmd = dmtp.Command(t=dmtp.Login, v=loc)
        # send command
        self.send_command(cmd=cmd, destination=destination)
        return True

    def __process_from(self, value: dmtp.LocationValue) -> bool:
        print('caller: %s' % value.to_dict())
        self.__locations[value.id] = value
        self.__locations[(value.ip, value.port)] = value
        return True

    def process_command(self, cmd: dmtp.Command, source: tuple, destination: tuple) -> bool:
        cmd_type = cmd.type
        cmd_value = cmd.value
        if cmd_type == dmtp.From:
            assert isinstance(cmd_value, dmtp.LocationValue), 'call from cmd error: %s' % cmd_value
            return self.__process_from(value=cmd_value)
        else:
            super().process_command(cmd=cmd, source=source, destination=destination)

    def process_message(self, msg: dmtp.Message, source: tuple, destination: tuple) -> bool:
        print('received msg: %s' % msg)
        return True


# create a hub for sockets
server_address = (SERVER_HOST, SERVER_PORT)
g_hub = udp.Hub()
g_hub.open(port=CLIENT_PORT)
g_hub.connect(destination=server_address)
g_hub.start()

# create client
g_client = Client(hub=g_hub)


def try_login():
    g_client.say_hi(destination=server_address)


def try_call(uid: str):
    f_id = dmtp.Field(t=dmtp.ID, v=dmtp.StringValue(string=uid))
    cmd = dmtp.Command(t=dmtp.Call, v=f_id)
    print('sending cmd: %s' % cmd)
    g_client.send_command(cmd=cmd, destination=server_address)


def send_text(uid: str, msg: str):
    location = g_client.location(uid=uid)
    if location is None or location.ip is None:
        print('cannot locate user: %s, %s' % (uid, location))
        return False
    address = (location.ip, location.port)
    content = msg.encode('utf-8')
    f_sender = dmtp.Field(t=dmtp.MsgSender, v=dmtp.StringValue(string=g_client.identifier))
    f_content = dmtp.Field(t=dmtp.MsgContent, v=dmtp.BinaryValue(data=content))
    msg = dmtp.Message(fields=[f_sender, f_content])
    print('sending msg: %s' % msg)
    g_client.send_message(msg=msg, destination=address)


if __name__ == '__main__':

    if len(sys.argv) == 2:
        g_client.identifier = sys.argv[1]

    # test send
    try_login()
    time.sleep(2)
    try_call(uid='albert')
    time.sleep(2)
    send_text(uid='albert', msg='Hello world!')
