package com.jutsuworks.geshop.domain.model

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith

class MoneyAndCartGroupTest {

    @Test
    fun `Money enforces non-negative integer cents and clamps discounts at zero`() {
        val price = Money(125_000L)
        val shipping = Money(15_000L)
        assertEquals(Money(140_000L), price + shipping)

        val discounted = price.applyDiscountClamped(Money(25_000L))
        assertEquals(100_000L, discounted.cents)

        val clampedZero = price.applyDiscountClamped(Money(500_000L))
        assertEquals(0L, clampedZero.cents)

        assertFailsWith<IllegalArgumentException> {
            Money(-1L)
        }
    }

    @Test
    fun `CartGroup computes shop subtotal and clamps shop voucher before shipping`() {
        val group = CartGroup(
            shopId = "shop-jade-01",
            shopName = "Jade Official Store",
            items = listOf(
                CartItem(skuId = "sku-1", title = "Mechanical Keyboard", unitPrice = Money(150_000L), quantity = 2),
                CartItem(skuId = "sku-2", title = "PBT Keycaps", unitPrice = Money(50_000L), quantity = 1),
            ),
            shopVoucherDiscount = Money(40_000L),
            shippingFee = Money(12_000L),
        )

        assertEquals(350_000L, group.rawSubtotal.cents)
        assertEquals(310_000L, group.subtotalAfterShopVoucher.cents)
        assertEquals(322_000L, group.totalPayableBeforePlatformVoucher.cents)
    }

    @Test
    fun `CartGroup clamps oversized shop voucher to zero subtotal without discounting shipping`() {
        val group = CartGroup(
            shopId = "shop-amber-02",
            shopName = "Amber Gadgets",
            items = listOf(
                CartItem(skuId = "sku-3", title = "USB-C Cable", unitPrice = Money(20_000L), quantity = 1),
            ),
            shopVoucherDiscount = Money(99_000L),
            shippingFee = Money(10_000L),
        )

        assertEquals(0L, group.subtotalAfterShopVoucher.cents)
        assertEquals(10_000L, group.totalPayableBeforePlatformVoucher.cents)
    }
}
