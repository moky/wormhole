# -*- coding: utf-8 -*-

from typing import Generic, Optional

from tcp import PlainPorter

from udp import SocketAddress
from udp import Connection, ConnectionState
from udp import Porter

from .utils import Log
from .auto import AutoGate, H


class UDPGate(AutoGate, Generic[H]):

    # # Override
    # def get_connection(self, remote: SocketAddress, local: Optional[SocketAddress]) -> Optional[Connection]:
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
    # def _cache_advance_party(self, data: bytes, source: SocketAddress, destination: Optional[SocketAddress],
    #                          connection: Connection) -> List[bytes]:
    #     # TODO: cache the advance party before decide which docker to use
    #     if data is None:
    #         return []
    #     else:
    #         return [data]
    #
    # # Override
    # def _clear_advance_party(self, source: SocketAddress, destination: Optional[SocketAddress],
    #                          connection: Connection):
    #     # TODO: remove advance party for this connection
    #     pass
    #
    # # Override
    # async def _heartbeat(self, connection: Connection):
    #     # let the client to do the job
    #     if isinstance(connection, ActiveConnection):
    #         await super()._heartbeat(connection=connection)
    #
    # def __kill(self, remote: SocketAddress = None, local: Optional[SocketAddress] = None,
    #            connection: Connection = None):
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
    # def get_docker(self, remote: SocketAddress, local: Optional[SocketAddress]) -> Optional[Porter]:
    #     worker = self._get_porter(remote=remote, local=local)
    #     if worker is None:
    #         worker = self._create_porter(remote=remote, local=local)
    #         assert worker is not None, 'failed to create docker: %s, %s' % (remote, local)
    #         self._set_porter(porter=worker, remote=remote, local=local)
    #     return worker

    async def send_data(self, payload: bytes, source: Optional[SocketAddress], destination: SocketAddress):
        worker = await self.fetch_porter(remote=destination, local=source)
        if worker is not None:
            await worker.send_data(payload=payload)
