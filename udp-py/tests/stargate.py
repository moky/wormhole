# -*- coding: utf-8 -*-

import time
import traceback
from typing import Generic, TypeVar, Optional, List

from startrek.types import Address
from startrek.fsm import Runnable, Daemon
from udp.ba import Data
from udp.mtp import DataType, Package
from udp import Connection, ConnectionState, ActiveConnection
from udp import GateDelegate
from udp import StarGate, Docker, PackageDocker


H = TypeVar('H')


class UDPGate(StarGate, Runnable, Generic[H]):

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
        try:
            incoming = self.hub.process()
            outgoing = super().process()
            return incoming or outgoing
        except Exception as error:
            print('[UDP] process error: %s' % error)
            traceback.print_exc()

    # Override
    def get_connection(self, remote: tuple, local: Optional[tuple]) -> Optional[Connection]:
        return self.hub.connect(remote=remote, local=local)

    # Override
    def _create_docker(self, remote: tuple, local: Optional[tuple],
                       advance_party: List[bytes]) -> Optional[PackageDocker]:
        # TODO: check data format before creating docker
        return PackageDocker(remote=remote, local=None, gate=self)

    # Override
    def _get_docker(self, remote: Address, local: Optional[Address]) -> Optional[PackageDocker]:
        return super()._get_docker(remote=remote, local=None)

    # Override
    def _set_docker(self, remote: tuple, local: Optional[tuple], docker: Docker):
        super()._set_docker(remote=remote, local=None, docker=docker)

    # Override
    def _remove_docker(self, remote: tuple, local: Optional[tuple], docker: Optional[Docker]):
        super()._remove_docker(remote=remote, local=None, docker=docker)

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
        self.error(msg='connection error: %s, %s (%s, %s)' % (error, connection, source, destination))

    def get_docker(self, remote: tuple, local: Optional[tuple], advance_party: List[bytes]) -> Optional[PackageDocker]:
        docker = self._get_docker(remote=remote, local=local)
        if docker is None:
            docker = self._create_docker(remote=remote, local=local, advance_party=advance_party)
            assert docker is not None, 'failed to create docker: %s, %s' % (remote, local)
            self._set_docker(remote=docker.remote_address, local=docker.local_address, docker=docker)
        return docker

    def send_package(self, pack: Package, source: Optional[tuple], destination: tuple) -> bool:
        docker = self.get_docker(remote=destination, local=source, advance_party=[])
        if docker is not None:
            return docker.send_package(pack=pack)

    def send_command(self, body: bytes, source: Optional[tuple], destination: tuple) -> bool:
        pack = Package.new(data_type=DataType.COMMAND, body=Data(buffer=body))
        return self.send_package(pack=pack, source=source, destination=destination)

    def send_message(self, body: bytes, source: Optional[tuple], destination: tuple) -> bool:
        pack = Package.new(data_type=DataType.MESSAGE, body=Data(buffer=body))
        return self.send_package(pack=pack, source=source, destination=destination)

    @classmethod
    def info(cls, msg: str):
        now = time.time()
        prefix = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(now))
        print('[%s] %s' % (prefix, msg))

    @classmethod
    def error(cls, msg: str):
        print('[ERROR] ', msg)
