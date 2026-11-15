# Requirements: `03-rust-flash-sale-and-split-orders` — Rust High-Concurrency Flash-Sale Engine & Split-Order Checkout

## EARS Acceptance Criteria
- **REQ-01:** WHEN 1,000 concurrent requests attempt to reserve the last 10 units of a Flash-Sale SKU in `apps/engine-rust/`, THE SYSTEM SHALL grant exactly 10 reservations and return `409 SOLD_OUT` to the remaining 990 with zero negative stock.