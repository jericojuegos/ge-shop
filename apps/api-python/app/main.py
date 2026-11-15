from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field

from app.core.config import settings
from app.core.database import Base, engine


class HealthResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: str = Field(default="ok")
    service: str = Field(default="ge-shop-api-python")
    money_unit: str = Field(default="cents_int64")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    Base.metadata.create_all(bind=engine)
    yield


def create_app() -> FastAPI:
    application = FastAPI(
        title="GE Shop Marketplace API",
        version="0.1.0",
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.get("/health", response_model=HealthResponse, tags=["system"])
    async def get_health() -> HealthResponse:
        return HealthResponse(
            status="ok",
            service=settings.app_name,
            money_unit="cents_int64",
        )

    return application


app = create_app()
