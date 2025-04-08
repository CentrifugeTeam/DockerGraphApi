import json
from io import StringIO

import networkx as nx
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from ...db import Network
from ...deps import Session
from ..graph.manager import graph_manager

r = APIRouter(prefix='/json')


def create_mindmap_from_networks(networks: list['Network'], data: dict):
    data['networks'] = []
    for network in networks:
        data['networks'].append(network.model_dump())


@r.get('', response_class=StreamingResponse)
async def plantuml(session: Session):

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
            neighbors.append({'name': graph.nodes[neighbor]['name']})
            create_mindmap_from_networks(
                graph.nodes[neighbor]['networks'], neighbor)

            visited.add(neighbor)

        create_mindmap_from_networks(
            graph.nodes[node]['networks'], host)
        hosts.append(host)
        visited.add(node)

    return StreamingResponse(StringIO.write(json.dumps(response)), media_type="application/json",
                             headers={
                                 "Content-Disposition": "attachment; filename=graph.puml",
                                 "Content-Type": "text/plain; charset=utf-8"})
