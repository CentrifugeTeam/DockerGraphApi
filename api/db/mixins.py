from sqlmodel import Field


class IDMixin:
    id: int | None = Field(default=None, primary_key=True)
