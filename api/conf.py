from datetime import timedelta

from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict
from redis.asyncio import ConnectionPool
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="postgres_")
    username: str = Field(validation_alias="postgres_user")
    password: str
    host: str
    port: int
    db: str

    @property
    def sqlalchemy_url(self) -> str:
        return str(
            PostgresDsn.build(
                scheme="postgresql+asyncpg",
                username=self.username,
                password=self.password,
                host=self.host,
                port=self.port,
                path=self.db,
            )
        )


class RedisSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="redis_")
    user: str
    password: str
    host: str
    port: int
    db: str


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="allow")
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    AUTH_TOKEN: str


settings = Settings()
engine = create_async_engine(settings.database.sqlalchemy_url)
session_maker = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession)
connection_pool = ConnectionPool(
    host=settings.redis.host, port=settings.redis.port, decode_responses=True)
