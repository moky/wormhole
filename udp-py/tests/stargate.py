# -*- coding: utf-8 -*-

import time
import traceback
import weakref
from threading import Thread
from typing import Generic, TypeVar, Optional, List

from startrek.fsm import Runnable
from udp.ba import Data
from udp.mtp import DataType, Package
from udp import Connection, ConnectionState, ActiveConnection
from udp import Gate, Hub
from udp import GateDelegate
from udp import StarGate, PackageDocker


class UDPDocker(PackageDocker):

    def __init__(self, remote: tuple, local: Optional[tuple], gate: Gate):
        super().__init__(remote=remote, local=local)
        self.__gate_ref = weakref.ref(gate)

    @property  # Override
    def gate(self) -> Gate:
        return self.__gate_ref()


H = TypeVar('H')


class UDPGate(StarGate, Runnable, Generic[H]):

    def __init__(self, delegate: GateDelegate, daemon: bool = False):
        super().__init__(delegate=delegate)
        self.__hub: H = None
        # running thread
        self.__thread: Optional[Thread] = None
        self.__running = False
        self.__daemon = daemon

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
        self.__force_stop()
        self.__running = True
        thr = Thread(target=self.run, daemon=self.__daemon)
        self.__thread = thr
        thr.start()
        return thr

    def __force_stop(self):
        self.__running = False
        t: Thread = self.__thread
        if t is not None:
            # waiting 2 seconds for stopping the thread
            self.__thread = None
            t.join(timeout=2.0)

    def stop(self):
        self.__force_stop()

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
            print('[UDP] process error: %s' % error)
            traceback.print_exc()

    # Override
    def get_connection(self, remote: tuple, local: Optional[tuple]) -> Optional[Connection]:
        hub = self.hub
        assert isinstance(hub, Hub), 'hub error: %s' % hub
        return hub.connect(remote=remote, local=local)

    # Override
    def _create_docker(self, remote: tuple, local: Optional[tuple],
                       advance_party: List[bytes]) -> Optional[PackageDocker]:
        # TODO: check data format before creating docker
        return UDPDocker(remote=remote, local=None, gate=self)

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
        if current == ConnectionState.ERROR:
            docker = self._get_docker(remote=connection.remote_address, local=connection.local_address)
            self.info(msg='closing docker: %s' % docker)
            if docker is not None:
                self._remove_docker(docker=docker)
                docker.close()
            self.info(msg='closing connection: %s' % connection)
            if connection.opened:
                connection.close()

    # Override
    def connection_error(self, error: ConnectionError, data: Optional[bytes],
                         source: Optional[tuple], destination: Optional[tuple], connection: Optional[Connection]):
        self.error(msg='ignore socket error: %s, %s' % (error, connection))

    def get_docker(self, remote: tuple, local: Optional[tuple]) -> Optional[PackageDocker]:
        docker = self._get_docker(remote=remote, local=local)
        if docker is None:
            docker = self._create_docker(remote=remote, local=local, advance_party=[])
            assert docker is not None, 'failed to create docker: %s, %s' % (remote, local)
            self._set_docker(docker=docker)
        return docker

    def send_package(self, pack: Package, source: Optional[tuple], destination: tuple) -> bool:
        docker = self.get_docker(remote=destination, local=source)
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
