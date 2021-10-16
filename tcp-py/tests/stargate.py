# -*- coding: utf-8 -*-

import threading
import time
from typing import Generic, TypeVar, Optional, List

from startrek.fsm import Runnable
from tcp import Connection, ConnectionState
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

    def start(self):
        self.__running = True
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
        time.sleep(0.125)

    # Override
    def process(self):
        hub = self.hub
        # from tcp import Hub
        # assert isinstance(hub, Hub)
        incoming = hub.process()
        outgoing = super().process()
        return incoming or outgoing

    # Override
    def get_connection(self, remote: tuple, local: Optional[tuple]) -> Optional[Connection]:
        hub = self.hub
        # from tcp import Hub
        # assert isinstance(hub, Hub)
        return hub.connect(remote=remote, local=local)

    # Override
    def _create_docker(self, remote: tuple, local: Optional[tuple], advance_party: List[bytes]) -> Optional[Docker]:
        # TODO: check data format before creating docker
        return PlainDocker(remote=remote, local=local, gate=self)

    # Override
    def _cache_advance_party(self, data: bytes, source: tuple, destination: Optional[tuple],
                             connection: Connection) -> List[bytes]:
        # TODO: cache the advance party before decide which docker to use
        if data is None:
            return []
        else:
            return [data]

    # Override
    def _clear_advance_party(self, source: tuple, destination: Optional[tuple], connection: Connection):
        # TODO: remove advance party for this connection
        pass

    # Override
    def connection_state_changed(self, previous: ConnectionState, current: ConnectionState, connection: Connection):
        super().connection_state_changed(previous=previous, current=current, connection=connection)
        self.info('connection state changed: %s -> %s, %s' % (previous, current, connection))

    def send_data(self, payload: bytes, source: Optional[tuple], destination: tuple):
        worker = self.get_docker(remote=destination, local=source, advance_party=[])
        if isinstance(worker, PlainDocker):
            worker.send_data(payload=payload)

    @classmethod
    def info(cls, msg: str):
        now = time.time()
        prefix = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(now))
        print('[%s] %s' % (prefix, msg))

    @classmethod
    def error(cls, msg: str):
        print('[ERROR] ', msg)
