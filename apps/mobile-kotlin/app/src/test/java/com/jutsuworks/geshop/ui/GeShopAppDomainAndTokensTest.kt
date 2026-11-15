package com.jutsuworks.geshop.ui

import com.jutsuworks.geshop.domain.MultiShopCartCalculator
import com.jutsuworks.geshop.domain.model.CartGroup
import com.jutsuworks.geshop.domain.model.CartItem
import com.jutsuworks.geshop.domain.model.Money
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.runBlocking
import kotlin.test.Test
import kotlin.test.assertEquals

class GeShopAppDomainAndTokensTest {

    @Test
    fun `Brand tokens match Jade Iron Amber design system specification`() {
        assertEquals(0xFFEA580CL, GeShopBrandTokens.PRIMARY_ACTION_HEX)
        assertEquals(0xFF0D9488L, GeShopBrandTokens.SECONDARY_TRUST_HEX)
        assertEquals(0xFF0F172AL, GeShopBrandTokens.DARK_SURFACE_HEX)
    }

    @Test
    fun `MultiShopCartCalculator sums multi-shop cart groups via pure Kotlin Flow`() = runBlocking {
        val groups = listOf(
            CartGroup(
                shopId = "shop-1",
                shopName = "Shop One",
                items = listOf(CartItem("sku-a", "Item A", Money(100_000L), 1)),
                shopVoucherDiscount = Money(10_000L),
                shippingFee = Money(5_000L),
            ),
            CartGroup(
                shopId = "shop-2",
                shopName = "Shop Two",
                items = listOf(CartItem("sku-b", "Item B", Money(200_000L), 1)),
                shopVoucherDiscount = Money(20_000L),
                shippingFee = Money(5_000L),
            ),
        )

        val total = MultiShopCartCalculator.observeTotalCents(flowOf(groups)).first()
        assertEquals(280_000L, total.cents)
    }
}
