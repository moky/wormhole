# -*- coding: utf-8 -*-

import time
from threading import Thread
from typing import Generic, TypeVar, Optional, List

from startrek.fsm import Runnable
from tcp import Connection, ConnectionState, BaseConnection
from tcp import Hub
from tcp import GateDelegate, Docker
from tcp import StarGate, PlainDocker


class TCPDocker(PlainDocker):

    @property  # Override
    def hub(self) -> Optional[Hub]:
        gate = self.gate
        if isinstance(gate, TCPGate):
            return gate.hub


H = TypeVar('H')


class TCPGate(StarGate, Runnable, Generic[H]):

    def __init__(self, delegate: GateDelegate):
        super().__init__(delegate=delegate)
        self.__hub: H = None
        # running thread
        self.__thread: Optional[Thread] = None
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
        self.__force_stop()
        self.__running = True
        t = Thread(target=self.run)
        self.__thread = t
        t.start()

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
        from tcp import Hub
        assert isinstance(hub, Hub)
        incoming = hub.process()
        outgoing = super().process()
        return incoming or outgoing

    # Override
    def get_connection(self, remote: tuple, local: Optional[tuple]) -> Optional[Connection]:
        hub = self.hub
        from tcp import Hub
        assert isinstance(hub, Hub)
        return hub.connect(remote=remote, local=local)

    # Override
    def _create_docker(self, remote: tuple, local: Optional[tuple], advance_party: List[bytes]) -> Optional[Docker]:
        # TODO: check data format before creating docker
        return TCPDocker(remote=remote, local=None, gate=self)

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
        if isinstance(connection, BaseConnection) and connection.is_activated:
            super()._heartbeat(connection=connection)

    def __kill(self, remote: tuple = None, local: Optional[tuple] = None, connection: Connection = None):
        # if conn is null, disconnect with (remote, local);
        # else, disconnect with connection when local address matched.
        hub = self.hub
        assert isinstance(hub, Hub), 'hub error: %s' % hub
        connection = hub.disconnect(remote=remote, local=local, connection=connection)
        # if connection is not activated, means it's a server connection,
        # remove the docker too.
        if isinstance(connection, BaseConnection):
            if not connection.is_activated:
                # remove docker for server connection
                remote = connection.remote_address
                local = connection.local_address
                self._remove_docker(remote=remote, local=local, docker=None)

    # Override
    def connection_state_changed(self, previous: ConnectionState, current: ConnectionState, connection: Connection):
        super().connection_state_changed(previous=previous, current=current, connection=connection)
        self.info('connection state changed: %s -> %s, %s' % (previous, current, connection))
        if current == ConnectionState.ERROR:
            self.error('remove error connection: %s' % connection)
            self.__kill(connection=connection)

    # Override
    def connection_error(self, error, data: Optional[bytes],
                         source: Optional[tuple], destination: Optional[tuple], connection: Optional[Connection]):
        if connection is None:
            # failed to receive data
            self.__kill(remote=source, local=destination)
        else:
            # failed to send data
            self.__kill(remote=destination, local=source, connection=connection)

    def get_docker(self, remote: tuple, local: Optional[tuple]) -> Optional[PlainDocker]:
        worker = self._get_docker(remote=remote, local=local)
        if worker is None:
            worker = self._create_docker(remote=remote, local=local, advance_party=[])
            assert worker is not None, 'failed to create docker: %s, %s' % (remote, local)
            self._put_docker(docker=worker)
        return worker

    def send_data(self, payload: bytes, source: Optional[tuple], destination: tuple) -> bool:
        worker = self.get_docker(remote=destination, local=source)
        if worker is not None:
            return worker.send_data(payload=payload)

    @classmethod
    def info(cls, msg: str):
        now = time.time()
        prefix = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(now))
        print('[%s] %s' % (prefix, msg))

    @classmethod
    def error(cls, msg: str):
        print('[ERROR] ', msg)
