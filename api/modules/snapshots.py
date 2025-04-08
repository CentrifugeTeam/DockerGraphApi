from datetime import datetime, timedelta, timezone
from functools import reduce
from uuid import UUID

from fastapi import APIRouter, WebSocket
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import joinedload
from sqlmodel import select

from ..db import Snapshot
from ..deps import RedisSession, Session
from .containers import ContainerBase, ContainerReadV2
from .graph import Graph

r = APIRouter(prefix="/snapshots", tags=["Snapshots"])


class Proxy:

    def __init__(self, proxied, hosts):
        self.proxied = proxied
        self.hosts = hosts

    def __getattr__(self, name):
        return getattr(self.proxied, name)


@r.get('', response_model=Graph)
async def graph(snap_datetime: datetime, session: Session, host_id: UUID | None = None, is_dead: bool | None = None):
    snapshot = (await  session.exec(select(Snapshot).where(Snapshot.datetime < snap_datetime).limit(1))).one_or_none()
    if not snapshot:
        {'nodes': [], 'links': [], 'network_to_network': []}
    else:
        return snapshot.snapshot
    # if host_id:
    #     stmt = select(Host).where(Host.id == host_id)
    #     if is_dead:
    #         stmt = stmt.join(Network, Network.host_id == Host.id).join(
    #             Container, Container.network_id == Network.id)
    #         nodes = (await session.exec(stmt.options(joinedload(Host.networks).subqueryload(Network.containers)))).unique().all()
    #         if nodes:
    #             for net in nodes[0].networks:
    #                 containers = [container for container in net.containers if container.last_active < datetime.now(
    #                     tz=timezone.utc) - timedelta(days=1)]
    #                 net.containers = containers
    #     else:
    #         nodes = (await session.exec(stmt.options(joinedload(Host.networks).subqueryload(Network.containers)))).unique()
    #     links = []
    #     net_to_net = []
    # else:
    #     if is_dead:
    #         stmt = select(Host).join(Network, Network.host_id == Host.id).join(
    #             Container, Container.network_id == Network.id)
    #         nodes = (await session.exec(stmt.options(joinedload(Host.networks).subqueryload(Network.containers)))).unique().all()
    #         node_ids = []
    #         networks_ids = []
    #         for host in nodes:
    #             node_ids.append(host.id)
    #             for net in host.networks:
    #                 containers = [container for container in net.containers if container.last_active < datetime.now(
    #                     tz=timezone.utc) - timedelta(days=1)]
    #                 net.containers = containers
    #                 networks_ids.append(net.id)
    #         with session.no_autoflush:
    #             links = await session.exec(select(HostToHost).where((HostToHost.source_host_id.in_(node_ids)) & (HostToHost.target_host_id.in_(node_ids))))
    #             net_to_net = await session.exec(select(NetworkToNetwork).where(NetworkToNetwork.source_network_id.in_(networks_ids), NetworkToNetwork.target_network_id.in_(networks_ids)))
    #         # TODO mock for now

    #     else:
    #         nodes = (await session.exec(select(Host).options(joinedload(Host.networks).subqueryload(Network.containers)))).unique()
    #         links = (await session.exec(select(HostToHost)))
    #         net_to_net = await session.exec(select(NetworkToNetwork))
    # return {'nodes': nodes, 'links': links, 'network_to_network': net_to_net}
