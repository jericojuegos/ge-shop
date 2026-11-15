from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field

from app.core.config import settings
from app.core.contracts import register_catalog_search, register_shop_lookup
from app.core.database import Base, engine
from app.modules.ai_search.router import router as ai_search_router
from app.modules.auth import models as auth_models  # noqa: F401
from app.modules.auth.router import router as auth_router
from app.modules.catalog import models as catalog_models  # noqa: F401
from app.modules.catalog.router import router as catalog_router
from app.modules.catalog.service import search_catalog_items
from app.modules.shops import models as shops_models  # noqa: F401
from app.modules.shops.router import router as shops_router
from app.modules.shops.service import lookup_user_shop_id


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
    register_shop_lookup(lookup_user_shop_id)
    register_catalog_search(search_catalog_items)

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

    application.include_router(auth_router)
    application.include_router(shops_router)
    application.include_router(catalog_router)
    application.include_router(ai_search_router)

    return application


app = create_app()
