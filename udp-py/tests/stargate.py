# -*- coding: utf-8 -*-

import socket
import time
from abc import ABC
from typing import Generic, TypeVar, Optional, Union

from startrek.types import SocketAddress
from startrek.skywalker import Runnable, Runner, Daemon
from startrek import Connection, ConnectionState
from startrek import ActiveConnection
from startrek import Hub
from startrek import Arrival
from startrek import Porter, PorterDelegate
from startrek import StarGate

from udp.mtp import Package
from udp import PackageArrival
from udp import PackagePorter


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

    async def send_message(self, body: Union[bytes, bytearray],
                           remote: SocketAddress, local: Optional[SocketAddress]) -> bool:
        docker = await self.fetch_porter(remote=remote, local=local)
        if isinstance(docker, PackagePorter):
            return await docker.send_message(body=body)

    async def send_command(self, body: Union[bytes, bytearray],
                           remote: SocketAddress, local: Optional[SocketAddress]) -> bool:
        docker = await self.fetch_porter(remote=remote, local=local)
        if isinstance(docker, PackagePorter):
            return await docker.send_command(body=body)

    async def send_package(self, pack: Package,
                           remote: SocketAddress, local: Optional[SocketAddress]) -> bool:
        docker = await self.fetch_porter(remote=remote, local=local)
        if isinstance(docker, PackagePorter):
            return await docker.send_package(pack=pack)

    #
    #   Docker
    #

    # Override
    def _create_porter(self, remote: SocketAddress, local: Optional[SocketAddress]) -> Porter:
        # TODO: check data format before creating docker
        docker = PackagePorter(remote=remote, local=local)
        docker.delegate = self.delegate
        return docker

    #
    #   Connection Delegate
    #

    # Override
    async def connection_state_changed(self, previous: Optional[ConnectionState], current: Optional[ConnectionState],
                                       connection: Connection):
        await super().connection_state_changed(previous=previous, current=current, connection=connection)
        Log.info(msg='connection state changed: %s -> %s, %s' % (previous, current, connection))

    # Override
    async def connection_failed(self, error: Union[IOError, socket.error], data: bytes, connection: Connection):
        await super().connection_failed(error=error, data=data, connection=connection)
        Log.error(msg='connection failed: %s, %s' % (error, connection))

    # Override
    async def connection_error(self, error: Union[IOError, socket.error], connection: Connection):
        # if isinstance(error, IOError) and str(error).startswith('failed to send: '):
        Log.error(msg='connection error: %s, %s' % (error, connection))


class Log:

    @classmethod
    def info(cls, msg: str):
        now = time.time()
        prefix = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(now))
        print('[%s]         | %s' % (prefix, msg))
        pass

    @classmethod
    def error(cls, msg: str):
        now = time.time()
        prefix = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(now))
        print('[%s]  ERROR  | %s' % (prefix, msg))
        pass
