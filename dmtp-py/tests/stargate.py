# -*- coding: utf-8 -*-

from typing import Generic, Optional

from udp.ba import Data
from udp.mtp import DataType, Package

from udp import SocketAddress
from udp import Connection, ConnectionState
from udp import Porter
from udp import PackagePorter

from .utils import Log
from .auto import AutoGate, H


class UDPGate(AutoGate, Generic[H]):

    # Override
    def _create_porter(self,  remote: SocketAddress, local: Optional[SocketAddress]) -> Porter:
        # TODO: check data format before creating docker
        docker = PackagePorter(remote=remote, local=None)
        docker.delegate = self.delegate
        return docker

    # Override
    async def connection_state_changed(self, previous: Optional[ConnectionState], current: Optional[ConnectionState],
                                       connection: Connection):
        await super().connection_state_changed(previous=previous, current=current, connection=connection)
        Log.info('connection state changed: %s -> %s, %s' % (previous, current, connection))

    async def send_package(self, pack: Package, source: Optional[SocketAddress], destination: SocketAddress) -> bool:
        worker = await self.fetch_porter(remote=destination, local=source)
        if isinstance(worker, PackagePorter):
            return await worker.send_package(pack=pack)
        else:
            assert False, 'package porter error: %s' % worker

    async def send_command(self, body: bytes, source: Optional[SocketAddress], destination: SocketAddress) -> bool:
        pack = Package.new(data_type=DataType.COMMAND, body=Data(buffer=body))
        return await self.send_package(pack=pack, source=source, destination=destination)

    async def send_message(self, body: bytes, source: Optional[SocketAddress], destination: SocketAddress) -> bool:
        pack = Package.new(data_type=DataType.MESSAGE, body=Data(buffer=body))
        return await self.send_package(pack=pack, source=source, destination=destination)
