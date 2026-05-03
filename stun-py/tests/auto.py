# -*- coding: utf-8 -*-

from abc import ABC
from typing import Generic, TypeVar, Optional

from startrek.skywalker import Runnable, Runner, Daemon

from udp import SocketAddress
from udp import Connection, ActiveConnection
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
