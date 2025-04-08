from pydantic import BaseModel


class NetworkCreate(BaseModel):
    name: str
    network_id: str


class NetworkRead(NetworkCreate):
    id: int


class OverlayNetworkCreate(NetworkCreate):
    peers: list[str]
