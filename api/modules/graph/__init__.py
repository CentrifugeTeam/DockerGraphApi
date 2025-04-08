from datetime import datetime, timedelta, timezone
from functools import reduce
from uuid import UUID

from fastapi import APIRouter, WebSocket
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import joinedload
from sqlmodel import select

from ...db import Container, Host, HostToHost, Network, NetworkToNetwork
from ...deps import RedisSession, Session
from ..containers import ContainerBase, ContainerReadV2
from ..hosts.scheme import HostRead
from ..networks import NetworkRead
from ..networks import manager as network_manager
from .manager import graph_manager


class NetworkLink(BaseModel):
    source_id: UUID
    target_id: UUID


class GraphNetworkRead(NetworkRead):
    containers: list[ContainerReadV2]


class GraphHostRead(HostRead):
    networks: list[GraphNetworkRead]


class NetworkToNetworkRead(BaseModel):
    source_id: int
    target_id: int


class Graph(BaseModel):
    nodes: list[GraphHostRead]
    links: list[NetworkLink]
    network_to_network: list[NetworkToNetworkRead]

    @field_validator('links', mode='before')
    @classmethod
    def validate(cls, links: list[HostToHost]):
        for link in links:
            yield {'source_id': link.source_host_id, 'target_id': link.target_host_id}

    @field_validator('network_to_network', mode='before')
    @classmethod
    def validate_ntn(cls, nets: list[NetworkToNetwork]):
        for net in nets:
            yield {'source_id': net.source_network_id, 'target_id': net.target_network_id}


r = APIRouter(prefix="/graph", tags=["Graph"])


class Proxy:

    def __init__(self, proxied, hosts):
        self.proxied = proxied
        self.hosts = hosts

    def __getattr__(self, name):
        return getattr(self.proxied, name)


@r.get('', response_model=Graph)
async def graph(session: Session, host_id: UUID | None = None, is_dead: bool | None = None):
    if host_id:
        stmt = select(Host).where(Host.id == host_id)
        if is_dead:
            stmt = stmt.join(Network, Network.host_id == Host.id).join(
                Container, Container.network_id == Network.id)
            nodes = (await session.exec(stmt.options(joinedload(Host.networks).subqueryload(Network.containers)))).unique().all()
            if nodes:
                for net in nodes[0].networks:
                    containers = [container for container in net.containers if container.last_active < datetime.now(
                        tz=timezone.utc) - timedelta(days=1)]
                    net.containers = containers
        else:
            nodes = (await session.exec(stmt.options(joinedload(Host.networks).subqueryload(Network.containers)))).unique()
        links = []
        net_to_net = []
    else:
        if is_dead:
            stmt = select(Host).join(Network, Network.host_id == Host.id).join(
                Container, Container.network_id == Network.id)
            nodes = (await session.exec(stmt.options(joinedload(Host.networks).subqueryload(Network.containers)))).unique().all()
            node_ids = []
            networks_ids = []
            for host in nodes:
                node_ids.append(host.id)
                for net in host.networks:
                    containers = [container for container in net.containers if container.last_active < datetime.now(
                        tz=timezone.utc) - timedelta(days=1)]
                    net.containers = containers
                    networks_ids.append(net.id)
            with session.no_autoflush:
                links = await session.exec(select(HostToHost).where((HostToHost.source_host_id.in_(node_ids)) & (HostToHost.target_host_id.in_(node_ids))))
                net_to_net = await session.exec(select(NetworkToNetwork).where(NetworkToNetwork.source_network_id.in_(networks_ids), NetworkToNetwork.target_network_id.in_(networks_ids)))
            # TODO mock for now

        else:
            nodes = (await session.exec(select(Host).options(joinedload(Host.networks).subqueryload(Network.containers)))).unique()
            links = (await session.exec(select(HostToHost)))
            net_to_net = await session.exec(select(NetworkToNetwork))
    return {'nodes': nodes, 'links': links, 'network_to_network': net_to_net}
