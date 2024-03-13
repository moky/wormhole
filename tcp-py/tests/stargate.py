# -*- coding: utf-8 -*-

import socket
import threading
import time
from abc import ABC
from typing import Generic, TypeVar, Optional, List, Union

from startrek.fsm import Runnable, Daemon
from startrek.types import SocketAddress
from startrek import Connection, ConnectionState
from startrek import ActiveConnection
from startrek import Hub
from startrek import Arrival
from startrek import Docker, DockerDelegate
from startrek import StarDocker, StarGate
from tcp import PlainArrival
from tcp import PlainDocker


H = TypeVar('H')


# noinspection PyAbstractClass
class CommonGate(StarGate, Generic[H], ABC):

    def __init__(self, delegate: DockerDelegate):
        super().__init__(delegate=delegate)
        self.__hub: H = None
        self.__lock = threading.Lock()

    @property
    def hub(self) -> H:
        return self.__hub

    @hub.setter
    def hub(self, h: H):
        self.__hub = h

    #
    #   Docker
    #

    # Override
    def _get_docker(self, remote: SocketAddress, local: Optional[SocketAddress]) -> Optional[Docker]:
        return super()._get_docker(remote=remote, local=None)

    # Override
    def _set_docker(self, docker: Docker,
                    remote: SocketAddress, local: Optional[SocketAddress]) -> Optional[Docker]:
        return super()._set_docker(docker=docker, remote=remote, local=None)

    # Override
    def _remove_docker(self, docker: Optional[Docker],
                       remote: SocketAddress, local: Optional[SocketAddress]) -> Optional[Docker]:
        return super()._remove_docker(docker=docker, remote=remote, local=None)

    def fetch_docker(self, advance_party: List[bytes], remote: SocketAddress, local: Optional[SocketAddress]) -> Docker:
        # try to get docker
        with self.__lock:
            old = self._get_docker(remote=remote, local=local)
            if old is None:  # and advance_party is not None:
                # create & cache docker
                worker = self._create_docker(advance_party, remote=remote, local=local)
                self._set_docker(worker, remote=remote, local=local)
            else:
                worker = old
        if old is None:
            hub = self.hub
            assert isinstance(hub, Hub), 'gate hub error: %s' % hub
            conn = hub.connect(remote=remote, local=local)
            if conn is None:
                # assert False, 'failed to get connection: %s -> %s' % (local, remote)
                self._remove_docker(worker, remote=remote, local=local)
                worker = None
            else:
                assert isinstance(worker, StarDocker), 'docker error: %s, %s' % (remote, worker)
                # set connection for this docker
                worker.set_connection(conn)
        return worker

    def send_response(self, payload: bytes, ship: Arrival,
                      remote: SocketAddress, local: Optional[SocketAddress]) -> bool:
        assert isinstance(ship, PlainArrival), 'arrival ship error: %s' % ship
        worker = self._get_docker(remote=remote, local=local)
        if worker is None:
            return False
        elif not worker.alive:
            return False
        else:
            return worker.send_data(payload=payload)

    # Override
    def _heartbeat(self, connection: Connection):
        # let the client to do the job
        if isinstance(connection, ActiveConnection):
            super()._heartbeat(connection=connection)

    # Override
    def _cache_advance_party(self, data: bytes, connection: Connection) -> List[bytes]:
        # TODO: cache the advance party before decide which docker to use
        if data is None or len(data) == 0:
            return []
        else:
            return [data]

    # Override
    def _clear_advance_party(self, connection: Connection):
        # TODO: remove advance party for this connection
        pass


# noinspection PyAbstractClass
class AutoGate(CommonGate, Runnable, Generic[H], ABC):

    def __init__(self, delegate: DockerDelegate, daemonic: bool = True):
        super().__init__(delegate=delegate)
        # running thread
        self.__daemon = Daemon(target=self.run, daemonic=daemonic)
        self.__running = False

    def start(self):
        self.__running = True
        self.__daemon.start()

    def stop(self):
        self.__running = False
        self.__daemon.stop()

    # Override
    def run(self):
        while self.__running:
            if not self.process():
                self._idle()

    # noinspection PyMethodMayBeStatic
    def _idle(self):
        time.sleep(0.125)

    # Override
    def process(self) -> bool:
        incoming = self.hub.process()
        outgoing = super().process()
        return incoming or outgoing


class TCPGate(AutoGate, Generic[H]):

    def send_message(self, payload: bytes,
                     remote: SocketAddress, local: SocketAddress) -> bool:
        docker = self.fetch_docker([], remote=remote, local=local)
        if docker is not None:
            return docker.send_data(payload=payload)

    #
    #   Docker
    #

    # Override
    def _create_docker(self, parties: List[bytes],
                       remote: SocketAddress, local: Optional[SocketAddress]) -> Docker:
        # TODO: check data format before creating docker
        docker = PlainDocker(remote=remote, local=local)
        docker.delegate = self.delegate
        return docker

    #
    #   Connection Delegate
    #

    # Override
    def connection_state_changed(self, previous: Optional[ConnectionState], current: Optional[ConnectionState],
                                 connection: Connection):
        super().connection_state_changed(previous=previous, current=current, connection=connection)
        self.info(msg='connection state changed: %s -> %s, %s' % (previous, current, connection))

    # Override
    def connection_failed(self, error: Union[IOError, socket.error], data: bytes, connection: Connection):
        super().connection_failed(error=error, data=data, connection=connection)
        self.error(msg='connection failed: %s, %s' % (error, connection))

    # Override
    def connection_error(self, error: Union[IOError, socket.error], connection: Connection):
        # if isinstance(error, IOError) and str(error).startswith('failed to send: '):
        self.error(msg='connection error: %s, %s' % (error, connection))

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
