#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import random

import sys
import os

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

    def sign_in(self, value: dmtp.LocationValue, source: tuple) -> bool:
        uid = value.id
        mapped_ip = value.ip
        mapped_port = value.port
        print('server ask sign for ID: %s, %s' % (uid, value.to_dict()))
        s = b'BASE64(signature)'
        loc = dmtp.LocationValue.new(uid=value.id, ip=mapped_ip, port=mapped_port, signature=s, nat=self.nat)
        cmd = dmtp.Command(t=dmtp.Login, v=loc)
        # send command
        self._peer.send_command(data=cmd.data, destination=source)
        return True

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
    f_id = dmtp.Field(t=dmtp.ID, v=dmtp.StringValue(string=g_client.identifier))
    cmd = dmtp.Command(t=dmtp.Login, v=f_id)
    print('sending cmd: %s' % cmd)
    g_client.send_command(cmd=cmd, destination=server_address)


def send_text(msg: str):
    content = msg.encode('utf-8')
    f_sender = dmtp.Field(t=dmtp.VarName('S'), v=dmtp.StringValue(string=g_client.identifier))
    f_content = dmtp.Field(t=dmtp.VarName('D'), v=dmtp.BinaryValue(data=content))
    msg = dmtp.Message(fields=[f_sender, f_content])
    print('sending msg: %s' % msg)
    g_client.send_message(msg=msg, destination=('127.0.0.1', 9901))


if __name__ == '__main__':
    # test send
    try_login()
    send_text(msg='Hello world!')
