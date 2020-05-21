
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


class Client(udp.Peer, udp.PeerDelegate):

    def __init__(self):
        super().__init__()
        self.delegate = self
        self.nat = 'Port Restricted Cone NAT'

    def __process_sign(self, value: dmtp.LocationValue, context: dict) -> bool:
        source = context['source']
        assert source is not None, 'source address error: %s' % context
        print('server ask sign for ID: %s, %s' % (value.id, value.to_dict()))
        # response
        _id = dmtp.Field(t=dmtp.ID,
                         v=dmtp.StringValue(string=value.id))
        _addr = dmtp.Field(t=dmtp.Address,
                           v=dmtp.MappedAddressValue(ip=value.ip, port=value.port))
        _s = dmtp.Field(t=dmtp.Signature,
                        v=dmtp.Value(data=b'BASE64(signature)'))
        _nat = dmtp.Field(t=dmtp.NAT,
                          v=dmtp.StringValue(string=self.nat))
        # command with fields
        _login = dmtp.Command(t=dmtp.Login,
                              v=dmtp.FieldsValue(fields=[_id, _addr, _s, _nat]))
        # send command
        self.send_command(data=_login.data, destination=source)
        return True

    def __process_cmd(self, cmd: dmtp.Command, context: dict):
        cmd_type = cmd.type
        cmd_value = cmd.value
        if cmd_type == dmtp.Sign:
            assert isinstance(cmd_value, dmtp.LocationValue), 'sign value error: %s' % cmd_value
            self.__process_sign(value=cmd_value, context=context)

    #
    #   PeerDelegate
    #
    def send_data(self, data: bytes, destination: tuple, source: Union[tuple, int] = None) -> int:
        return g_hub.send(data=data, destination=destination, source=source)

    def received_command(self, cmd: bytes, source: tuple, destination: tuple) -> bool:
        context = {
            'source': source,
            'destination': destination,
        }
        commands = dmtp.Command.parse_all(data=cmd)
        for cmd in commands:
            self.__process_cmd(cmd=cmd, context=context)
        return True

    def received_message(self, msg: bytes, source: tuple, destination: tuple) -> bool:
        print('received msg from %s to %s: %s' % (source, destination, msg))
        return True


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
