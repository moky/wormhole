# -*- coding: utf-8 -*-

import threading
import time
from typing import Generic, TypeVar, Optional, List

from startrek.fsm import Runnable
from udp.ba import Data
from udp.mtp import DataType, Package
from udp import Connection
from udp import GateDelegate, Docker
from udp import StarGate
from udp import PackageDocker


H = TypeVar('H')


class UDPGate(StarGate, Runnable, Generic[H]):

    def __init__(self, delegate: GateDelegate):
        super().__init__(delegate=delegate)
        self.__running = False
        self.__hub: H = None

    @property
    def hub(self) -> H:
        return self.__hub

    @hub.setter
    def hub(self, h: H):
        self.__hub = h

    def start(self):
        threading.Thread(target=self.run).start()

    def stop(self):
        self.__running = False

    @property
    def running(self) -> bool:
        return self.__running

    # Override
    def run(self):
        self.__running = True
        while self.running:
            if not self.process():
                self._idle()

    # noinspection PyMethodMayBeStatic
    def _idle(self):
        time.sleep(0.078125)

    # Override
    def process(self):
        hub = self.hub
        # from tcp import Hub
        # assert isinstance(hub, Hub)
        activated = hub.process()
        busy = super().process()
        return activated or busy

    # Override
    def get_connection(self, remote: tuple, local: Optional[tuple]) -> Optional[Connection]:
        hub = self.hub
        # from tcp import Hub
        # assert isinstance(hub, Hub)
        return hub.get_connection(remote=remote, local=local)

    # Override
    def create_docker(self, remote: tuple, local: Optional[tuple], advance_party: List[bytes]) -> Optional[Docker]:
        # TODO: check data format before creating docker
        return PackageDocker(remote=remote, local=local, gate=self)

    # Override
    def cache_advance_party(self, data: bytes, source: tuple, destination: Optional[tuple],
                            connection: Connection) -> List[bytes]:
        # TODO: cache the advance party before decide which docker to use
        if data is None:
            return []
        else:
            return [data]

    # Override
    def clear_advance_party(self, source: tuple, destination: Optional[tuple], connection: Connection):
        # TODO: remove advance party for this connection
        pass

    def send_command(self, body: bytes, source: Optional[tuple], destination: tuple):
        pack = Package.new(data_type=DataType.COMMAND, body=Data(buffer=body))
        worker = self.get_docker(remote=destination, local=source, advance_party=[])
        if isinstance(worker, PackageDocker):
            worker.send_package(pack=pack)

    def send_message(self, body: bytes, source: Optional[tuple], destination: tuple):
        pack = Package.new(data_type=DataType.MESSAGE, body=Data(buffer=body))
        worker = self.get_docker(remote=destination, local=source, advance_party=[])
        if isinstance(worker, PackageDocker):
            worker.send_package(pack=pack)

    @classmethod
    def info(cls, msg: str):
        print('> ', msg)

    @classmethod
    def error(cls, msg: str):
        print('ERROR> ', msg)
