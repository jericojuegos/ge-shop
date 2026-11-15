package com.jutsuworks.geshop.domain.model

@JvmInline
value class Money(val cents: Long) : Comparable<Money> {
    init {
        require(cents >= 0L) { "Money cents must be non-negative, got $cents" }
    }

    operator fun plus(other: Money): Money = Money(Math.addExact(this.cents, other.cents))

    fun multiplyQuantity(quantity: Int): Money {
        require(quantity > 0) { "Quantity must be positive, got $quantity" }
        return Money(Math.multiplyExact(this.cents, quantity.toLong()))
    }

    fun applyDiscountClamped(discount: Money): Money {
        val net = (this.cents - discount.cents).coerceAtLeast(0L)
        return Money(net)
    }

    override fun compareTo(other: Money): Int = this.cents.compareTo(other.cents)

    companion object {
        val ZERO = Money(0L)
    }
}
