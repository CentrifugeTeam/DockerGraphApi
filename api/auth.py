
from fastapi import APIRouter, Depends

from .deps import get_agent


class AuthAPIRouter(APIRouter):
    def __init__(self, *args, **kwargs):
        return super().__init__(
            *args, **kwargs, dependencies=[Depends(get_agent)],
            responses={401: {'detail': 'Unauthorized'},
                       403: {'detail': 'Forbidden'}},
        )
