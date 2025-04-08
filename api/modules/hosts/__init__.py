from contextlib import suppress
from uuid import UUID

from fastapi import APIRouter
from sqlalchemy.orm import joinedload
from sqlmodel import select

from ...db import Host
from ...deps import Agent, Session
from ..networks.scheme import NetworkRead
from ..hosts.scheme import HostRead, HostUpdate
from .scheme import HostRead
from fastapi_sqlalchemy_toolkit import ModelManager

manager = ModelManager(Host)

r = APIRouter(prefix="/hosts", tags=["Hosts"])


class HostNetworksRead(HostRead):
    networks: list[NetworkRead]


@r.get("", response_model=list[HostNetworksRead])
async def hosts(session: Session, host_id: UUID | None = None):
    stmt = select(Host)
    if host_id:
        stmt = stmt.where(Host.id == host_id)
    return (await session.exec(stmt.options(joinedload(Host.networks)))).unique()



@r.patch('/{id}', response_model=HostUpdate)
async def container(id: UUID, obj: HostUpdate, session: Session):
    """Добавление контейнеров на основе сети и хоста"""
    obj_db = await manager.get_or_404(session, id=id)
    return await manager.update(session, obj_db, obj)
