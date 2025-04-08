from fastapi import HTTPException
from pydantic import BaseModel


class ErrorModel(BaseModel):
    detail: str | dict[str, str]


def to_openapi(exception: HTTPException):
    return {
        exception.status_code: {
            "detail": exception.detail,
            "headers": exception.headers,
            "description": exception.detail,
            "model": ErrorModel,
        }
    }
