# 📋 Product Requirements Document (PRD) — GE Shop (`ge-shop` · Spec Track B)

## 1. Product Vision
**GE Shop** is a clean-room, polyglot Multi-Vendor Marketplace (inspired by Shopee, Lazada, and Amazon) combining:
- **`apps/api-python/` (Python FastAPI Core API):** Standalone JWT Auth, Multi-Vendor Seller Shops, Catalog, Stacked Voucher Engine, Split-Shop Order Orchestrator, and **Gemini AI** Semantic Product Discovery.
- **`apps/engine-rust/` (Rust Axum High-Concurrency Engine):** Ultra-low-latency Flash-Sale Countdown Pool & Atomic Stock Reservation microservice.
- **`apps/mobile-kotlin/` (Kotlin Jetpack Compose Mobile App):** Offline-first Android Buyer & Seller POS app.

## 2. User Roles & Actors
- **Buyer:** Registers/logs in, searches products via Gemini semantic search, adds items from multiple Seller Shops into one cart, stacks Shop + Platform + Free Shipping vouchers, claims Flash-Sale deals, and pays once to generate per-shop sub-orders.
- **Seller (`shop_id` Tenant):** Onboards a Shop, manages SKUs and Shop Vouchers, nominates SKUs into Flash-Sale pools, fulfills shop sub-orders, and receives escrow payouts upon order completion.
- **Platform Admin:** Manages platform-wide vouchers, flash-sale time slots, and escrow commission splits.