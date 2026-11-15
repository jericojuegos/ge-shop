# Requirements: `02-multi-shop-cart-and-vouchers` — Multi-Shop Grouped Cart & Stacked Voucher Engine (Shop + Platform + Shipping)

## EARS Acceptance Criteria
- **REQ-01:** WHEN a buyer applies both a Seller Shop Voucher and a Platform Voucher to a multi-shop cart, THE SYSTEM SHALL deduct the Shop Voucher from that shop's subtotal first, clamp at zero, and apply the Platform Voucher in integer cents.