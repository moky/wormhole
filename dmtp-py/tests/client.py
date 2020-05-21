
import time
from typing import Union

import sys
import os

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

import udp
import dmtp


SERVER_HOST = '127.0.0.1'
SERVER_PORT = 9394

CLIENT_PORT = 9527


class Client(dmtp.Client):

    def __init__(self):
        super().__init__()
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
        self.send_command(data=cmd.data, destination=source)
        return True

    def process_message(self, msg: dmtp.Message, source: tuple, destination: tuple) -> bool:
        print('received msg: %s' % msg.to_dict())
        return True

    def process_file(self, file: dmtp.Message, source: tuple, destination: tuple) -> bool:
        print('received file: %s' % file.filename)
        return True

    #
    #   PeerDelegate
    #
    def send_data(self, data: bytes, destination: tuple, source: Union[tuple, int] = None) -> int:
        return g_hub.send(data=data, destination=destination, source=source)


# create a hub for sockets
server_address = (SERVER_HOST, SERVER_PORT)
g_hub = udp.Hub()
g_hub.open(port=CLIENT_PORT)
g_hub.connect(destination=server_address)
g_hub.start()

# create client
g_client = Client()
g_client.start()
g_hub.add_listener(listener=g_client)


def try_login():
    identifier = 'moky'
    f_id = dmtp.Field(t=dmtp.ID, v=dmtp.StringValue(string=identifier))
    cmd = dmtp.Command(t=dmtp.Login, v=f_id)
    print('sending cmd: %s' % cmd)
    g_client.send_command(data=cmd.data, destination=server_address)


def send_text(msg: str):
    sender = 'moky'
    content = msg.encode('utf-8')
    f_sender = dmtp.Field(t=dmtp.VarName('S'), v=dmtp.StringValue(string=sender))
    f_content = dmtp.Field(t=dmtp.VarName('D'), v=dmtp.BinaryValue(data=content))
    msg = dmtp.Message(fields=[f_sender, f_content])
    print('sending msg: %s' % msg)
    g_client.send_message(data=msg.data, destination=('127.0.0.1', 8888))


if __name__ == '__main__':
    # test send
    try_login()
    send_text(msg='Hello world!')
    # exit
    g_client.stop()
    time.sleep(2)
    g_hub.stop()
