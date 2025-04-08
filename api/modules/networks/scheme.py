from pydantic import BaseModel


class NetworkCreate(BaseModel):
    name: str
    network_id: str
    display_name: str | None = None
    packets_number: int = 0


class NetworkRead(NetworkCreate):
    id: int


class OverlayNetworkCreate(NetworkCreate):
    peers: list[str]


class NetworkUpdate(BaseModel):
    display_name: str | None = None
