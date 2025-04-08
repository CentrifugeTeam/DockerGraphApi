from datetime import datetime
from uuid import UUID

from fastapi import HTTPException, status
from fastapi_sqlalchemy_toolkit import ModelManager, make_partial_model
from pydantic import BaseModel
from sqlmodel import delete, select

from ..auth import AuthAPIRouter
from ..db import Container, Network
from ..deps import Agent, Session
from .networks.scheme import NetworkCreate, NetworkRead

r = AuthAPIRouter(prefix='/containers')
manager = ModelManager(Container)


class ContainerBase(BaseModel):
    name: str
    image: str
    container_id: str
    status: str
    packets_number: int | None = None
    ip: str
    created_at: datetime
    last_active: datetime | None


class ContainerCreate(ContainerBase):
    network_ids: list[int]


ContainerUpdate = make_partial_model(ContainerBase)


class ContainerReadV2(ContainerBase):
    id: int


class ContainerReadV1(ContainerBase):
    id: int
    host_id: UUID


class ContainerBatchCreate(ContainerBase):
    network_ids: list[str]


class ContainersBatchCreate(BaseModel):
    networks: list[NetworkCreate]
    containers: list[ContainerBatchCreate]


class Proxy:

    def __init__(self, proxied, host_id):
        self.proxied = proxied
        self.host_id = host_id

    def host_id(self):
        return self.host_id

    def __getattr__(self, name):
        return getattr(self.proxied, name)


class ContainersBatchRead(BaseModel):
    networks: list[NetworkRead]
    containers: list[ContainerReadV1]


@r.post('/batch', response_model=ContainersBatchRead, responses={
    404: {'detail': 'Object not found', "content": {"application/json": {"example": {'detail': 'Host Not Found'}}}}})
async def batch_create(batch: ContainersBatchCreate, session: Session, agent: Agent):
    """Route был сделан как helper для создания нескольких контейнеров с сетями одновременно, нужно записать произвольные значения network.id чтобы сделать ссылку в объекте контейнера на сеть главное чтобы он не повторялся  , в запросе этот network.id меняется."""
    containers = []
    network_lookup = {}
    networks = []
    for network in batch.networks:
        network_db = (await session.exec(select(Network).where(Network.network_id == network.network_id).where(Network.host_id == agent.id))).one_or_none()
        if not network_db:
            network_db = Network(
                name=network.name, network_id=network.network_id, host_id=agent.id)
            session.add(network_db)
        network_lookup[network.network_id] = network_db

    for container in batch.containers:
        network_id = container.network_ids[0]  # Mock for now
        network_db = network_lookup[network_id]
        container_db = (await session.exec(select(Container).join(Network, Network.id == Container.network_id).where(Container.container_id == container.container_id).where(Network.network_id == network_id).where(Network.host_id == network_db.host_id))).one_or_none()
        if not container_db:
            container_db = Container(
                **container.model_dump(exclude={'network_ids'}))
            container_db.network = network_db
            session.add(container_db)

        networks.append(network_db)
        containers.append(Proxy(container_db, network_db.host_id))
    await session.commit()
    cons = await session.exec(select(Container).join(Network, Network.id == Container.network_id).where(
        Container.id.not_in([container.id for container in containers]
                            )).where(Network.host_id == agent.id))
    for container in cons:
        await session.delete(container)
    stmt = delete(Network).where(Network.id.not_in(
        [network.id for network in networks])).where(Network.host_id == agent.id)
    await session.exec(stmt)
    await session.commit()

    return {'networks': networks, 'containers': containers}


@r.post('', status_code=status.HTTP_204_NO_CONTENT, responses={
    404: {'detail': 'Object not found', "content": {"application/json": {"example": {'detail': 'Host Not Found'}}}}
})
async def containers(containers: list[ContainerCreate], session: Session, agent: Agent):
    """Добавление контейнеров на основе сети и хоста"""
    for container in containers:
        container_db = Container(
            **container.model_dump(exclude={'network_ids'}))
        container_db.host = agent

        network_id = container.network_ids[0]  # Mock for now
        network_db = await session.get(Network, network_id)
        if not network_db:
            raise HTTPException(
                status_code=404, detail='Network not found')

        container_db.network = network_db
        session.add(container_db)
    await session.commit()

    return


@r.patch('/{id}')
async def container(id: int, container: ContainerUpdate, session: Session):
    """Добавление контейнеров на основе сети и хоста"""
    container_db = await manager.get_or_404(session, id=id)
    return await manager.update(session, container_db, container)
