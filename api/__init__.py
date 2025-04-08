from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .modules import auth, containers, export, graph, hosts, networks

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(graph.r)
app.include_router(containers.r)
app.include_router(auth.r)
app.include_router(networks.r)
app.include_router(hosts.r)
app.include_router(export.r)
