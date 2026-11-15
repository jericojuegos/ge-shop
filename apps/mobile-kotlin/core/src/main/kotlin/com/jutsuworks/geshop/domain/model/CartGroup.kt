package com.jutsuworks.geshop.domain.model

data class CartItem(
    val skuId: String,
    val title: String,
    val unitPrice: Money,
    val quantity: Int,
) {
    init {
        require(skuId.isNotBlank()) { "skuId must not be blank" }
        require(quantity > 0) { "quantity must be > 0" }
    }

    val lineSubtotal: Money
        get() = unitPrice.multiplyQuantity(quantity)
}

data class CartGroup(
    val shopId: String,
    val shopName: String,
    val items: List<CartItem>,
    val shopVoucherDiscount: Money = Money.ZERO,
    val shippingFee: Money = Money.ZERO,
) {
    init {
        require(shopId.isNotBlank()) { "shopId must not be blank" }
        require(items.isNotEmpty()) { "CartGroup must contain at least one item" }
    }

    val rawSubtotal: Money
        get() = items.fold(Money.ZERO) { acc, item -> acc + item.lineSubtotal }

    val subtotalAfterShopVoucher: Money
        get() = rawSubtotal.applyDiscountClamped(shopVoucherDiscount)

    val totalPayableBeforePlatformVoucher: Money
        get() = subtotalAfterShopVoucher + shippingFee
}
