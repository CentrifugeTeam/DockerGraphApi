from sqlalchemy.orm import joinedload
from sqlmodel import select

from ...db import Host, HostToHost, Network
from ...deps import Session


class GraphManager:

    async def get_graph(self, session: Session, options=()):
        nodes = (await session.exec(select(Host).options(joinedload(Host.networks).subqueryload(Network.containers)))).unique()
        edges = (await session.exec(select(HostToHost)))
        return nodes, edges


graph_manager = GraphManager()
