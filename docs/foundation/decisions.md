# 🏛️ Architecture Decisions (ADR) — GE Shop

1. **ADR-01: Polyglot Right-Sizing:** Python FastAPI handles rich domain orchestration, Auth, and Gemini AI search; Rust handles CPU/concurrency-critical Flash-Sale inventory reservation; Kotlin Compose delivers native mobile UX.
2. **ADR-02: Parent Checkout -> Per-Shop Sub-Orders:** When a buyer checks out a cart containing items from N shops, `orders` creates 1 `CheckoutPaymentGroup` and N `ShopOrder` records so each seller fulfills independently and escrow settles per shop.
3. **ADR-03: Stacked Voucher Order:** `Shop Voucher` applies to that shop's subtotal first; `Platform Voucher` applies proportionally across eligible shop subtotals second; `Shipping Voucher` discounts shipping fees third.