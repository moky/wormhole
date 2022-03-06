# -*- coding: utf-8 -*-

import time
import traceback
from typing import Generic, TypeVar, Optional, List

from startrek.types import Address
from startrek.fsm import Runnable, Daemon
from tcp import Connection, ConnectionState, ActiveConnection
from tcp import Hub
from tcp import GateDelegate
from tcp import StarGate, PlainDocker


H = TypeVar('H')


class TCPGate(StarGate, Runnable, Generic[H]):

    def __init__(self, delegate: GateDelegate, daemonic: bool = True):
        super().__init__(delegate=delegate)
        self.__hub: H = None
        # running thread
        self.__daemon = Daemon(target=self.run, daemonic=daemonic)
        self.__running = False

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
        self.stop()
        self.__running = True
        return self.__daemon.start()

    def stop(self):
        self.__running = False
        self.__daemon.stop()

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
    def process(self) -> bool:
        hub = self.hub
        assert isinstance(hub, Hub), 'hub error: %s' % hub
        try:
            incoming = hub.process()
            outgoing = super().process()
            return incoming or outgoing
        except Exception as error:
            print('[TCP] process error: %s' % error)
            traceback.print_exc()

    # Override
    def get_connection(self, remote: tuple, local: Optional[tuple]) -> Optional[Connection]:
        hub = self.hub
        assert isinstance(hub, Hub), 'hub error: %s' % hub
        return hub.connect(remote=remote, local=None)

    # Override
    def _create_docker(self, remote: tuple, local: Optional[tuple],
                       advance_party: List[bytes]) -> Optional[PlainDocker]:
        # TODO: check data format before creating docker
        return PlainDocker(remote=remote, local=local, gate=self)

    # Override
    def _get_docker(self, remote: Address, local: Optional[Address]) -> Optional[PlainDocker]:
        return super()._get_docker(remote=remote, local=None)

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
    def _heartbeat(self, connection: Connection):
        # let the client to do the job
        if isinstance(connection, ActiveConnection):
            super()._heartbeat(connection=connection)

    # Override
    def connection_state_changed(self, previous: ConnectionState, current: ConnectionState, connection: Connection):
        super().connection_state_changed(previous=previous, current=current, connection=connection)
        self.info('connection state changed: %s -> %s, %s' % (previous, current, connection))

    # Override
    def connection_error(self, error: ConnectionError, data: Optional[bytes],
                         source: Optional[tuple], destination: Optional[tuple], connection: Optional[Connection]):
        # if isinstance(error, IOError) and str(error).startswith('failed to send: '):
        self.error(msg='connection error: %s' % error)

    def get_docker(self, remote: tuple, local: Optional[tuple], advance_party: List[bytes]) -> Optional[PlainDocker]:
        docker = self._get_docker(remote=remote, local=local)
        if docker is None:
            docker = self._create_docker(remote=remote, local=local, advance_party=advance_party)
            assert docker is not None, 'failed to create docker: %s, %s' % (remote, local)
            self._set_docker(docker=docker)
        return docker

    def send_data(self, payload: bytes, source: Optional[tuple], destination: tuple) -> bool:
        docker = self.get_docker(remote=destination, local=source, advance_party=[])
        if docker is not None:
            return docker.send_data(payload=payload)

    @classmethod
    def info(cls, msg: str):
        now = time.time()
        prefix = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(now))
        print('[%s] %s' % (prefix, msg))
        pass

    @classmethod
    def error(cls, msg: str):
        print('[ERROR] ', msg)
        pass
