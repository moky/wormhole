# -*- coding: utf-8 -*-
import socket
import time
from abc import ABC
from typing import Generic, TypeVar, Optional, List, Union

from startrek.fsm import Runnable, Daemon
from startrek.types import SocketAddress
from startrek import Channel, Connection, ConnectionState
from startrek import Hub
from startrek import Arrival
from startrek import Docker, DockerDelegate
from startrek import StarGate
from udp.mtp import Package
from udp import PackageArrival
from udp import PackageDocker


H = TypeVar('H')


class BaseGate(StarGate, Generic[H], ABC):

    def __init__(self, delegate: DockerDelegate):
        super().__init__(delegate=delegate)
        self.__hub: H = None

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
                    remote: SocketAddress, local: Optional[SocketAddress]):
        super()._set_docker(docker=docker, remote=remote, local=None)

    # Override
    def _remove_docker(self, docker: Optional[Docker],
                       remote: SocketAddress, local: Optional[SocketAddress]) -> Optional[Docker]:
        return super()._remove_docker(docker=docker, remote=remote, local=None)

    # # Override
    # def _heartbeat(self, connection: Connection):
    #     # let the client to do the job
    #     if isinstance(connection, ActiveConnection):
    #         super()._heartbeat(connection=connection)

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


class CommonGate(BaseGate, Generic[H], ABC):

    def __init__(self, delegate: DockerDelegate):
        super().__init__(delegate=delegate)
        self.__running = False

    @property
    def running(self) -> bool:
        return self.__running

    def start(self):
        self.__running = True

    def stop(self):
        self.__running = False

    def get_channel(self, remote: Optional[SocketAddress], local: Optional[SocketAddress]) -> Optional[Channel]:
        hub = self.hub
        assert isinstance(hub, Hub), 'gate hub error: %s' % hub
        return hub.open(remote=remote, local=local)

    def send_response(self, payload: bytes, ship: Arrival,
                      remote: SocketAddress, local: Optional[SocketAddress]) -> bool:
        assert isinstance(ship, PackageArrival), 'arrival ship error: %s' % ship
        docker = self._get_docker(remote=remote, local=local)
        if docker is not None:
            return docker.send_data(payload=payload)

    def fetch_docker(self, remote: SocketAddress, local: Optional[SocketAddress], advance_party: List[bytes]) -> Docker:
        docker = self._get_docker(remote=remote, local=local)
        if docker is None:  # and advance_party is not None:
            hub = self.hub
            assert isinstance(hub, Hub), 'gate hub error: %s' % hub
            conn = hub.connect(remote=remote, local=local)
            if conn is not None:
                docker = self._create_docker(connection=conn, advance_party=advance_party)
                if docker is None:
                    assert False, 'failed to create docker: %s, %s' % (remote, local)
                else:
                    self._set_docker(docker=docker, remote=docker.remote_address, local=docker.local_address)
        return docker


class AutoGate(CommonGate, Runnable, Generic[H], ABC):

    def __init__(self, delegate: DockerDelegate, daemonic: bool = True):
        super().__init__(delegate=delegate)
        # running thread
        self.__daemon = Daemon(target=self.run, daemonic=daemonic)

    def start(self):
        super().start()
        return self.__daemon.start()

    def stop(self):
        super().stop()
        self.__daemon.stop()

    # Override
    def run(self):
        while self.running:
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


class UDPGate(AutoGate, Generic[H]):

    def send_message(self, body: Union[bytes, bytearray],
                     remote: SocketAddress, local: Optional[SocketAddress]) -> bool:
        docker = self.fetch_docker(remote=remote, local=local, advance_party=[])
        if isinstance(docker, PackageDocker):
            return docker.send_message(body=body)

    def send_command(self, body: Union[bytes, bytearray],
                     remote: SocketAddress, local: Optional[SocketAddress]) -> bool:
        docker = self.fetch_docker(remote=remote, local=local, advance_party=[])
        if isinstance(docker, PackageDocker):
            return docker.send_command(body=body)

    def send_package(self, pack: Package,
                     remote: SocketAddress, local: Optional[SocketAddress]) -> bool:
        docker = self.fetch_docker(remote=remote, local=local, advance_party=[])
        if isinstance(docker, PackageDocker):
            return docker.send_package(pack=pack)

    #
    #   Docker
    #

    # Override
    def _create_docker(self, connection: Connection, advance_party: List[bytes]) -> Optional[Docker]:
        # TODO: check data format before creating docker
        docker = PackageDocker(connection=connection)
        docker.delegate = self.delegate
        return docker

    #
    #   Connection Delegate
    #

    # Override
    def connection_state_changed(self, previous: ConnectionState, current: ConnectionState, connection: Connection):
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
