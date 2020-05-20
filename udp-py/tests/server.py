from typing import Union

import sys
import os

curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

import udp


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

    #
    #   PeerDelegate
    #
    def send_data(self, data: bytes, destination: tuple, source: Union[tuple, int] = None) -> int:
        return g_hub.send(data=data, destination=destination, source=source)

    def received_command(self, cmd: bytes, source: tuple, destination: tuple) -> bool:
        print('received cmd from %s to %s: %s' % (source, destination, cmd))
        return True

    def received_message(self, msg: bytes, source: tuple, destination: tuple) -> bool:
        print('received msg from %s to %s: %s' % (source, destination, msg))
        return True


if __name__ == '__main__':
    # create server
    server = Server()
    server.start()
    g_hub.add_listener(listener=server)
