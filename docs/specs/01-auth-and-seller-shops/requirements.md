# Requirements: `01-auth-and-seller-shops` — Standalone JWT Auth, Seller Shops, Multi-Vendor Catalog & Gemini Search

## EARS Acceptance Criteria
- **REQ-01:** WHEN a seller creates or modifies a product SKU, THE SYSTEM SHALL enforce JWT `shop_id` ownership and reject cross-shop mutations with `403 FORBIDDEN`.