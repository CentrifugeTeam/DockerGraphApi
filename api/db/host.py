from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import ConfigDict
from sqlalchemy import Column, DateTime, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

from .mixins import IDMixin


class HostToHost(SQLModel, table=True):
    __tablename__ = 'host_to_host'
    source_host_id: UUID = Field(foreign_key="hosts.id", primary_key=True)
    target_host_id: UUID = Field(foreign_key="hosts.id", primary_key=True)


class NetworkToNetwork(SQLModel, table=True):
    __tablename__ = 'network_to_network'
    source_network_id: int = Field(foreign_key="networks.id", primary_key=True)
    target_network_id: int = Field(foreign_key="networks.id", primary_key=True)


class Host(SQLModel, table=True):
    __tablename__ = "hosts"
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    hostname: str
    ip: str
    token: str
    networks: list['Network'] = Relationship(
        back_populates='host')


class Network(IDMixin, SQLModel, table=True):
    __tablename__ = "networks"
    name: str
    network_id: str
    host_id: UUID = Field(foreign_key="hosts.id")
    containers: list['Container'] = Relationship(back_populates='network')

    host: 'Host' = Relationship(back_populates='networks')
    __table_args__ = (UniqueConstraint('network_id', 'host_id'),)


class Container(IDMixin, SQLModel, table=True):
    __tablename__ = "containers"
    model_config = ConfigDict(extra='allow')
    name: str
    container_id: str
    image: str
    status: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(
        tz=timezone.utc), sa_column=Column(DateTime(timezone=True), nullable=False))
    ip: str
    last_active: datetime = Field(default_factory=lambda: datetime.now(
        tz=timezone.utc), sa_column=Column(DateTime(timezone=True), nullable=False))
    network_id: int = Field(foreign_key="networks.id")
    network: Network = Relationship(back_populates="containers")
    packets_number: int = 0

    __table_args__ = (UniqueConstraint('container_id', 'network_id'),)
