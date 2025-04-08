from contextlib import suppress

from fastapi import HTTPException
from sqlalchemy.orm import joinedload
from sqlmodel import select

from ...auth import AuthAPIRouter
from ...db import Host, HostToHost, Network
from ...deps import Agent, Session
from .scheme import NetworkCreate, NetworkRead, OverlayNetworkCreate

r = AuthAPIRouter(prefix="/networks")


@r.post("", response_model=list[NetworkRead])
async def networks(networks: list[NetworkCreate], session: Session, agent: Agent):
    """Добавление Docker Networks"""
    response = []
    for network in networks:
        stmt = (
            select(Network)
            .where(Network.network_id == network.network_id)
            .where(Network.host_id == agent.id)
        )
        network_db = (await session.exec(stmt)).one_or_none()
        if not network_db:
            network_db = Network(**network.model_dump())
            network_db.host = agent
            session.add(network_db)

        response.append(network_db)

    await session.commit()
    return response


@r.post("/overlay", response_model=NetworkRead, responses={
    400: {"description": "At least 1 peers required"}
})
async def overlay(overlay: OverlayNetworkCreate, session: Session, agent: Agent):
    """Добавление Docker Overlay Network"""
    if len(overlay.peers) < 1:
        raise HTTPException(
            status_code=400, detail="At least 1 peers required")

    available_peers = set(overlay.peers) - {agent.ip}
    if len(available_peers) == 0:
        raise HTTPException(
            status_code=400, detail="At least 1 peers required without this host")

    stmt = (
        select(Network)
        .where(Network.network_id == overlay.network_id)
        .where(Network.host_id == agent.id)
    )
    network_db = (await session.exec(stmt)).one_or_none()
    if not network_db:

        # Maybe NAT can brake this logic because ip can repeat on different hosts
        hosts = []
        for peer in available_peers:
            host = (await session.exec(select(Host).where(Host.ip == peer))).one_or_none()
            if not host:
                continue
            hosts.append(host)

        if len(hosts) >= 1:
            for host in hosts:
                edge = (await session.exec(select(HostToHost).where(((HostToHost.source_host_id == host.id ) & (HostToHost.target_host_id == agent.id)) | ((HostToHost.target_host_id == host.id )& (HostToHost.source_host_id == agent.id))))).one_or_none()
                if not edge:
                    session.add(HostToHost(source_host_id=host.id, target_host_id=agent.id))
                    
        network_db = Network(**overlay.model_dump(exclude={'peers'}))
        network_db.host = agent
        session.add(network_db)
        
    # TODO create logic for delete peers

    await session.commit()
    return network_db
