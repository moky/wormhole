from typing import Union

import sys
import os

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

import udp
import dmtp


SERVER_HOST = '0.0.0.0'
SERVER_PORT = 9394

# create a hub for sockets
g_hub = udp.Hub()
g_hub.open(host=SERVER_HOST, port=SERVER_PORT)
g_hub.start()


class Server(udp.Peer, udp.PeerDelegate):

    def __init__(self):
        super().__init__()
        self.delegate = self

    def __send_sign(self, value: dmtp.LocationValue, context: dict) -> bool:
        source = context['source']
        assert source is not None, 'source address error: %s' % context
        print('user %s from %s: %s' % (value.id, source, value.to_dict()))
        # response
        _id = dmtp.Field(t=dmtp.ID,
                         v=dmtp.StringValue(string=value.id))
        _addr = dmtp.Field(t=dmtp.Address,
                           v=dmtp.MappedAddressValue(ip=source[0], port=source[1]))
        # command with fields
        _sign = dmtp.Command(t=dmtp.Sign,
                             v=dmtp.FieldsValue(fields=[_id, _addr]))
        # send command
        self.send_command(data=_sign.data, destination=source)
        return True

    def __accept_signature(self, value: dmtp.LocationValue) -> bool:
        uid = value.id
        ip = value.ip
        port = value.port
        s = value.signature
        print('user %s login from (%s:%d): %s' % (uid, ip, port, value.to_dict()))
        # TODO: save login info
        return True

    def __process_login(self, value: dmtp.LocationValue, context: dict) -> bool:
        if value.ip is None:
            return self.__send_sign(value=value, context=context)
        else:
            return self.__accept_signature(value=value)

    def __process_cmd(self, cmd: dmtp.Command, context: dict):
        cmd_type = cmd.type
        cmd_value = cmd.value
        if cmd_type == dmtp.Login:
            assert isinstance(cmd_value, dmtp.LocationValue), 'login value error: %s' % cmd_value
            self.__process_login(value=cmd_value, context=context)

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


if __name__ == '__main__':
    # create server
    server = Server()
    server.start()
    g_hub.add_listener(listener=server)
