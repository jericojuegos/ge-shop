from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.ai_search.schemas import AISearchRequest, AISearchResponse
from app.modules.ai_search.service import search_products_semantic

router = APIRouter(prefix="/api/v1/ai-search", tags=["ai-search"])


@router.post("/search", response_model=AISearchResponse)
async def semantic_search(
    payload: AISearchRequest,
    db: Annotated[Session, Depends(get_db)],
) -> AISearchResponse:
    return await search_products_semantic(db, payload)
