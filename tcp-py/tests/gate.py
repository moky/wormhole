# -*- coding: utf-8 -*-

import threading
import time
from typing import Generic, TypeVar, Optional, List

from startrek.fsm import Runnable
from tcp import Connection
from tcp import GateDelegate, Docker
from tcp import StarGate
from tcp import PlainDocker


H = TypeVar('H')


class TCPGate(StarGate, Runnable, Generic[H]):

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

    @property
    def running(self) -> bool:
        return self.__running

    def start(self):
        threading.Thread(target=self.run).start()

    def stop(self):
        self.__running = False

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
        return PlainDocker(remote=remote, local=local, gate=self)

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

    def send_payload(self, payload: bytes, source: Optional[tuple], destination: tuple):
        worker = self.get_docker(remote=destination, local=source, advance_party=[])
        if isinstance(worker, PlainDocker):
            worker.send_data(payload=payload)

    @classmethod
    def info(cls, msg: str):
        print('> ', msg)

    @classmethod
    def error(cls, msg: str):
        print('ERROR> ', msg)
