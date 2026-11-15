from __future__ import annotations

from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.core.ai_client import (
    SemanticSearchIntent,
    extract_search_intent,
    sanitize_search_query,
)
from app.core.contracts import CatalogItemSummary, fetch_active_catalog_items
from app.modules.ai_search.schemas import (
    AISearchRequest,
    AISearchResponse,
    AISearchResultItem,
)


def score_catalog_item(item: CatalogItemSummary, intent: SemanticSearchIntent) -> int:
    """Compute a deterministic relevance score for a catalog item against parsed intent."""
    title_lower = item.title.lower()
    desc_lower = item.description.lower()
    category_lower = item.category.lower()

    score = 0
    matched_text = False
    for kw in intent.keywords:
        kw_lower = kw.lower()
        if kw_lower in title_lower:
            score += 30
            matched_text = True
        elif kw_lower in desc_lower:
            score += 12
            matched_text = True
        elif kw_lower in category_lower:
            score += 10
            matched_text = True

    if intent.category_hint and category_lower == intent.category_hint.lower():
        score += 25
        if intent.keywords == ["product"]:
            matched_text = True

    if not matched_text and intent.keywords != ["product"]:
        return 0

    if item.total_stock_qty > 0:
        score += 5
    return score


async def search_products_semantic(
    db: Session,
    payload: AISearchRequest,
) -> AISearchResponse:
    """Parse natural-language search intent via Gemini/fallback and rank catalog hits."""
    sanitized_query = sanitize_search_query(payload.query)
    intent, provider = await extract_search_intent(sanitized_query)

    effective_category = payload.category or intent.category_hint
    effective_max_price = (
        payload.max_price_cents
        if payload.max_price_cents is not None
        else intent.max_price_cents
    )

    candidates = await run_in_threadpool(
        fetch_active_catalog_items,
        db,
        category=effective_category,
        max_price_cents=effective_max_price,
    )
    if not candidates and effective_category is not None and payload.category is None:
        # Broaden search if inferred category had zero hits while explicit category wasn't set.
        candidates = await run_in_threadpool(
            fetch_active_catalog_items,
            db,
            category=None,
            max_price_cents=effective_max_price,
        )

    scored: list[AISearchResultItem] = []
    for item in candidates:
        score = score_catalog_item(item, intent)
        if score <= 0:
            continue
        scored.append(
            AISearchResultItem(
                product_id=item.product_id,
                shop_id=item.shop_id,
                title=item.title,
                description=item.description,
                category=item.category,
                min_price_cents=item.min_price_cents,
                sku_count=item.sku_count,
                total_stock_qty=item.total_stock_qty,
                relevance_score=score,
            )
        )

    if intent.sort_by == "price_asc":
        scored.sort(key=lambda r: (r.min_price_cents, -r.relevance_score, r.product_id))
    elif intent.sort_by == "price_desc":
        scored.sort(key=lambda r: (-r.min_price_cents, -r.relevance_score, r.product_id))
    else:
        scored.sort(key=lambda r: (-r.relevance_score, r.min_price_cents, r.product_id))

    return AISearchResponse(
        query=sanitized_query,
        provider=provider,
        intent=intent,
        results=scored[: payload.limit],
    )
