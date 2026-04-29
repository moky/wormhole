# -*- coding: utf-8 -*-

from abc import ABC
from typing import Generic, TypeVar, Optional

from startrek.skywalker import Runnable, Runner, Daemon

from tcp import PlainPorter

from udp import SocketAddress
from udp import Connection, ConnectionState, ActiveConnection
from udp import Hub, Arrival, PackageArrival
from udp import PorterDelegate, Porter
from udp import StarGate

from .utils import Log


H = TypeVar('H')


# noinspection PyAbstractClass
class CommonGate(StarGate, Generic[H], ABC):

    def __init__(self, delegate: PorterDelegate):
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
    def _get_porter(self, remote: SocketAddress, local: Optional[SocketAddress]) -> Optional[Porter]:
        return super()._get_porter(remote=remote, local=None)

    # Override
    def _set_porter(self, porter: Porter,
                    remote: SocketAddress, local: Optional[SocketAddress]) -> Optional[Porter]:
        return super()._set_porter(porter=porter, remote=remote, local=None)

    # Override
    def _remove_porter(self, porter: Optional[Porter],
                       remote: SocketAddress, local: Optional[SocketAddress]) -> Optional[Porter]:
        return super()._remove_porter(porter=porter, remote=remote, local=None)

    async def fetch_porter(self, remote: SocketAddress, local: Optional[SocketAddress]) -> Optional[Porter]:
        # get connection from hub
        hub = self.hub
        assert isinstance(hub, Hub), 'gate hub error: %s' % hub
        conn = await hub.connect(remote=remote, local=local)
        if conn is not None:
            # connected, get docker with this connection
            return await self._dock(connection=conn, new_porter=True)
        assert False, 'failed to get connection: %s -> %s' % (local, remote)

    async def send_response(self, payload: bytes, ship: Arrival,
                            remote: SocketAddress, local: Optional[SocketAddress]) -> bool:
        assert isinstance(ship, PackageArrival), 'arrival ship error: %s' % ship
        docker = self._get_porter(remote=remote, local=local)
        if docker is None:
            return False
        elif not docker.alive:
            return False
        else:
            return await docker.send_data(payload=payload)

    # Override
    async def _heartbeat(self, connection: Connection):
        # let the client to do the job
        if isinstance(connection, ActiveConnection):
            await super()._heartbeat(connection=connection)


# noinspection PyAbstractClass
class AutoGate(CommonGate, Runnable, Generic[H], ABC):

    def __init__(self, delegate: PorterDelegate):
        super().__init__(delegate=delegate)
        self.__daemon = Daemon(target=self)
        self.__running = False

    @property
    def running(self) -> bool:
        return self.__running

    async def start(self):
        if self.running:
            assert False, 'auto gate is running: %s' % self
            # return False
        # 1. mark this gate to running
        self.__running = True
        # 2. start an async task for this gate
        self.__daemon.start()
        # await self.run()
        return True

    async def stop(self):
        # 1. mark this gate to stopped
        self.__running = False
        # 2. waiting for the gate to stop
        await Runner.sleep(seconds=0.25)
        # 3. cancel the async task
        self.__daemon.stop()

    # Override
    async def run(self):
        await self.setup()
        try:
            await self.handle()
        finally:
            await self.finish()

    async def setup(self):
        self.__running = True

    async def finish(self):
        self.__running = False

    async def handle(self):
        while self.running:
            if await self.process():
                # process() return true,
                # means this thread is busy,
                # so process next task immediately
                pass
            else:
                # nothing to do now,
                # have a rest ^_^
                await self._idle()
        Log.info(msg='auto gate stopped: %s' % self)

    # noinspection PyMethodMayBeStatic
    async def _idle(self):
        await Runner.sleep(seconds=0.125)

    # Override
    async def process(self) -> bool:
        try:
            incoming = await self.hub.process()
            outgoing = await super().process()
            return incoming or outgoing
        except Exception as error:
            Log.error(msg='process error: %s' % error)


class UDPGate(AutoGate, Generic[H]):

    # # Override
    # def get_connection(self, remote: tuple, local: Optional[tuple]) -> Optional[Connection]:
    #     hub = self.hub
    #     from udp import Hub
    #     assert isinstance(hub, Hub)
    #     return hub.connect(remote=remote, local=local)

    # Override
    def _create_porter(self,  remote: SocketAddress, local: Optional[SocketAddress]) -> Porter:
        # TODO: check data format before creating docker
        docker = PlainPorter(remote=remote, local=None)
        docker.delegate = self.delegate
        return docker

    # # Override
    # def _cache_advance_party(self, data: bytes, source: tuple, destination: Optional[tuple],
    #                          connection: Connection) -> List[bytes]:
    #     # TODO: cache the advance party before decide which docker to use
    #     if data is None:
    #         return []
    #     else:
    #         return [data]
    #
    # # Override
    # def _clear_advance_party(self, source: tuple, destination: Optional[tuple], connection: Connection):
    #     # TODO: remove advance party for this connection
    #     pass
    #
    # # Override
    # async def _heartbeat(self, connection: Connection):
    #     # let the client to do the job
    #     if isinstance(connection, ActiveConnection):
    #         await super()._heartbeat(connection=connection)
    #
    # def __kill(self, remote: tuple = None, local: Optional[tuple] = None, connection: Connection = None):
    #     # if conn is null, disconnect with (remote, local);
    #     # else, disconnect with connection when local address matched.
    #     hub = self.hub
    #     assert isinstance(hub, Hub), 'hub error: %s' % hub
    #     conn = hub.disconnect(remote=remote, local=local, connection=connection)
    #     # if connection is not activated, means it's a server connection,
    #     # remove the docker too.
    #     if conn is not None and not isinstance(conn, ActiveConnection):
    #         # remove docker for server connection
    #         remote = conn.remote_address
    #         local = conn.local_address
    #         self._remove_docker(remote=remote, local=local, docker=None)

    # Override
    async def connection_state_changed(self, previous: Optional[ConnectionState], current: Optional[ConnectionState],
                                       connection: Connection):
        await super().connection_state_changed(previous=previous, current=current, connection=connection)
        Log.info('connection state changed: %s -> %s, %s' % (previous, current, connection))

    # # Override
    # def connection_error(self, error: OSError, connection: Connection):
    #     source = connection.local_address
    #     destination = connection.remote_address
    #     if connection is None:
    #         # failed to receive data
    #         self.__kill(remote=source, local=destination)
    #     else:
    #         # failed to send data
    #         self.__kill(remote=destination, local=source, connection=connection)
    #
    # def get_docker(self, remote: tuple, local: Optional[tuple]) -> Optional[Porter]:
    #     worker = self._get_porter(remote=remote, local=local)
    #     if worker is None:
    #         worker = self._create_porter(remote=remote, local=local)
    #         assert worker is not None, 'failed to create docker: %s, %s' % (remote, local)
    #         self._set_porter(porter=worker, remote=remote, local=local)
    #     return worker

    async def send_data(self, payload: bytes, source: Optional[tuple], destination: tuple):
        worker = await self.fetch_porter(remote=destination, local=source)
        if worker is not None:
            await worker.send_data(payload=payload)
