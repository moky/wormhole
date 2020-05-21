
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
    _id = dmtp.StringValue(string=identifier)
    field = dmtp.Field(dmtp.ID, _id)
    cmd = dmtp.Command(dmtp.Login, field)
    print('sending cmd: %s' % cmd)
    g_client.send_command(data=cmd.data, destination=server_address)


if __name__ == '__main__':
    # test send
    while True:
        try_login()
        time.sleep(5)
