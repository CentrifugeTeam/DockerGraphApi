from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from redis.asyncio import Redis
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from .conf import connection_pool, session_maker
from .db import Host


async def get_session():
    async with session_maker() as session:
        yield session


async def get_redis():
    async with Redis(connection_pool=connection_pool) as r:
        yield r


Session = Annotated[AsyncSession, Depends(get_session)]
RedisSession = Annotated[Redis, Depends(get_redis)]

schema = HTTPBearer()


async def get_agent(session: Session, token=Depends(schema)):  # noqa: B008
    host = (await session.exec(select(Host).where(Host.token == token.credentials))).one_or_none()
    if not host:
        raise HTTPException(status_code=401, detail='Unauthorized')
    return host


Agent = Annotated[Host, Depends(get_agent)]
