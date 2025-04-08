
from secrets import token_hex
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlmodel import select

from ..conf import settings
from ..db import Host
from ..deps import Session
from .hosts.scheme import HostCreate, HostRead

r = APIRouter(prefix='/auth')


class Register(BaseModel):
    host: HostCreate
    token: str


class Registered(BaseModel):
    host: HostRead
    agent_id: UUID
    token: str


@r.post('', response_model=Registered, responses={
    401: {'description': 'Unauthorized'}
})
async def auth(register: Register, session: Session):
    if register.token != settings.AUTH_TOKEN:
        raise HTTPException(status_code=401, detail='Unauthorized')
    host = (await session.exec(select(Host).where(Host.hostname == register.host.hostname, Host.ip == register.host.ip))).one_or_none()
    if host:
        return {'host': host, 'agent_id': host.id, 'token': host.token}

    agent_id = uuid4()
    token = token_hex(16)
    host = Host(agent_id=agent_id, hostname=register.host.hostname,
                ip=register.host.ip, token=token)

    session.add(host)
    await session.commit()

    return {'host': host, 'agent_id': agent_id, 'token': token}
