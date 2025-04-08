from uuid import UUID

from pydantic import BaseModel


class HostCreate(BaseModel):
    hostname: str
    ip: str


class HostRead(HostCreate):
    id: UUID
