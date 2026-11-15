package com.jutsuworks.geshop.domain

import com.jutsuworks.geshop.domain.model.CartGroup
import com.jutsuworks.geshop.domain.model.Money
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

/**
 * Pure Kotlin domain flow calculator for multi-shop cart totals.
 * Contains zero android.* or androidx.* imports.
 */
object MultiShopCartCalculator {
    fun observeTotalCents(groupsFlow: Flow<List<CartGroup>>): Flow<Money> =
        groupsFlow.map { groups ->
            groups.fold(Money.ZERO) { acc, group ->
                acc + group.totalPayableBeforePlatformVoucher
            }
        }
}
