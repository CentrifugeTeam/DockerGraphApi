from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from .modules import auth, containers, export, graph, hosts, networks

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=10, compresslevel=5)

app.include_router(graph.r)
app.include_router(containers.r)
app.include_router(auth.r)
app.include_router(networks.r)
app.include_router(hosts.r)
app.include_router(export.r)
