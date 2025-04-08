from io import BytesIO
from uuid import UUID

import matplotlib.pyplot as plt
import networkx as nx
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from ...deps import Session
from ..graph.manager import graph_manager

r = APIRouter(prefix='/png')


@r.get('', response_class=StreamingResponse)
async def png(session: Session, id: UUID | None = None):
    if id:
        nodes, edges = await graph_manager.get_graph_by_id(session, id)
    else:
        nodes, edges = await graph_manager.get_graph(session)
    G = nx.Graph()
    labels = {}
    for node in nodes:
        G.add_node(node.id, type='host')
        labels[node.id] = "Host:"+node.hostname
        for net in node.networks:
            G.add_node(f'net_{net.id}', type='network')
            labels[f'net_{net.id}'] = "Network:"+net.name
            for container in net.containers:
                G.add_node(f"cont_{container.id}", type='container')
                labels[f"cont_{container.id}"] = "Container:"+container.name
                G.add_edge(f"cont_{container.id}",
                           f"net_{net.id}", type='container_network')
            G.add_edge(node.id, f"net_{net.id}", type='host_network')

    host_edges = [(edge.source_host_id, edge.target_host_id) for edge in edges]
    G.add_edges_from(host_edges
                     )

    pos = nx.spring_layout(G)

    plt.switch_backend('agg')

    # Create the figure
    plt.figure(figsize=(12, 8))

    # Draw networks and containers with different colors
    host_nodes = [node for node, attr in G.nodes(
        data=True) if attr.get("type") == "host"]
    network_nodes = [node for node, attr in G.nodes(
        data=True) if attr.get("type") == "network"]
    container_nodes = [node for node, attr in G.nodes(
        data=True) if attr.get("type") == "container"]

    # Draw nodes
    nx.draw_networkx_nodes(G, pos, nodelist=host_nodes,
                           node_color="lightblue", node_size=1000, alpha=0.8)
    nx.draw_networkx_nodes(G, pos, nodelist=network_nodes,
                           node_color="lightblue", node_size=800, alpha=0.8)
    nx.draw_networkx_nodes(G, pos, nodelist=container_nodes,
                           node_color="lightgreen", node_size=500, alpha=0.8)
    contains_edges = [(u, v) for u, v, attr in G.edges(
        data=True) if attr.get("type") == "container_network"]
    host_network = [(u, v) for u, v, attr in G.edges(
        data=True) if attr.get("type") == "host_network"]

    nx.draw_networkx_edges(G, pos, edgelist=contains_edges,
                           edge_color="gray", style="dashed", alpha=0.7)
    nx.draw_networkx_edges(G, pos, edgelist=host_network,
                           edge_color="gray", style="dashed", alpha=0.7)
    nx.draw_networkx_edges(G, pos, edgelist=host_edges,
                           edge_color="red", width=2)

    nx.draw_networkx_labels(G, pos, labels=labels,
                            font_size=10, font_family="sans-serif")

    plt.title("Network and Container Relationships")
    plt.axis("off")
    plt.tight_layout()

    # Instead of displaying, save to a bytes buffer
    buf = BytesIO()
    plt.savefig(buf, format="PNG", dpi=300)
    plt.close()
    buf.seek(0)

    return StreamingResponse(buf, media_type="image/png",
                             headers={
                                 "Content-Disposition": "attachment; filename=graph.png",
                                 "Content-Type": "image/png; charset=utf-8"})
