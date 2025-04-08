from contextlib import suppress
from uuid import UUID

from fastapi import APIRouter
from sqlalchemy.orm import joinedload
from sqlmodel import select

from ...db import Host
from ...deps import Agent, Session
from ..networks.scheme import NetworkRead
from .scheme import HostRead

r = APIRouter(prefix="/hosts")


class HostNetworksRead(HostRead):
    networks: list[NetworkRead]


@r.get("", response_model=list[HostNetworksRead])
async def hosts(session: Session, host_id: UUID | None = None):
    stmt = select(Host)
    if host_id:
        stmt = stmt.where(Host.id == host_id)
    return (await session.exec(stmt.options(joinedload(Host.networks)))).unique()
