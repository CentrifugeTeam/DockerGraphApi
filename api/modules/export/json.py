import json
from io import StringIO
from uuid import UUID

import networkx as nx
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from ...db import Network
from ...deps import Session
from ..graph.manager import graph_manager

r = APIRouter(prefix='/json')


def create_mindmap_from_networks(networks: list['Network']):
    data = []
    for network in networks:
        data.append({**network.model_dump(exclude={'host_id', "containers"}),
                    'containers': [cont.model_dump(exclude={'network_id', 'last_active', 'created_at'}) for cont in network.containers]})
    return data


@r.get('', response_class=StreamingResponse)
async def plantuml(session: Session, id: UUID | None = None):
    if id:
        nodes, edges = await graph_manager.get_graph_by_id(session, id)
    else:
        nodes, edges = await graph_manager.get_graph(session)
    graph = nx.Graph()
    graph.add_nodes_from(
        [(node.id, {'name': node.hostname, "networks": node.networks}) for node in nodes])
    graph.add_edges_from(
        [(edge.source_host_id, edge.target_host_id) for edge in edges])
    response = {'title': 'Docker Network', 'hosts': []}
    hosts = response['hosts']
    visited = set()
    for node in graph.nodes():
        if node in visited:
            continue
        host = {'name': graph.nodes[node]['name'],  'neighbors': []}
        neighbors = host['neighbors']
        for neighbor in graph.neighbors(node):
            if neighbor in visited:
                continue
            networks = create_mindmap_from_networks(
                graph.nodes[neighbor]['networks'])

            neighbors.append(
                {'name': graph.nodes[neighbor]['name'], 'networks': networks})

            visited.add(neighbor)

        networks = create_mindmap_from_networks(
            graph.nodes[node]['networks'])
        host['networks'] = networks
        hosts.append(host)
        visited.add(node)

    buffer = StringIO()
    buffer.write(json.dumps(response))
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/json",
                             headers={
                                 "Content-Disposition": "attachment; filename=graph.json",
                                 "Content-Type": "application/json; charset=utf-8"})
