from uuid import UUID

from pydantic import BaseModel




class HostCreate(BaseModel):
    hostname: str
    ip: str
    display_name: str | None = None
    
class HostUpdate(BaseModel):
    display_name: str | None = None


class HostRead(HostCreate):
    id: UUID
