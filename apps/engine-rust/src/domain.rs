use serde::{Deserialize, Serialize};
use std::sync::atomic::{AtomicI64, Ordering};

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub struct Money(pub i64);

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum MoneyError {
    NegativeAmount(i64),
    Overflow,
}

impl Money {
    pub fn new(cents: i64) -> Result<Self, MoneyError> {
        if cents < 0 {
            return Err(MoneyError::NegativeAmount(cents));
        }
        Ok(Self(cents))
    }

    pub const fn zero() -> Self {
        Self(0)
    }

    pub const fn cents(self) -> i64 {
        self.0
    }

    pub fn checked_add(self, other: Self) -> Result<Self, MoneyError> {
        self.0
            .checked_add(other.0)
            .ok_or(MoneyError::Overflow)
            .and_then(Self::new)
    }

    pub fn apply_discount_clamped(self, discount_cents: i64) -> Result<Self, MoneyError> {
        if discount_cents < 0 {
            return Err(MoneyError::NegativeAmount(discount_cents));
        }
        let net = (self.0 - discount_cents).max(0);
        Ok(Self(net))
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum StockError {
    InvalidInitialStock(i64),
    InvalidQuantity(i64),
    SoldOut { requested: i64, available: i64 },
}

#[derive(Debug)]
pub struct StockPool {
    sku_id: String,
    flash_price: Money,
    remaining: AtomicI64,
}

impl StockPool {
    pub fn new(sku_id: impl Into<String>, flash_price: Money, initial_stock: i64) -> Result<Self, StockError> {
        if initial_stock < 0 {
            return Err(StockError::InvalidInitialStock(initial_stock));
        }
        Ok(Self {
            sku_id: sku_id.into(),
            flash_price,
            remaining: AtomicI64::new(initial_stock),
        })
    }

    pub fn sku_id(&self) -> &str {
        &self.sku_id
    }

    pub fn flash_price(&self) -> Money {
        self.flash_price
    }

    pub fn available(&self) -> i64 {
        self.remaining.load(Ordering::Acquire)
    }

    /// Atomically reserves `qty` units using a lock-free CAS loop.
    /// Guarantees remaining stock never drops below zero under concurrent contention.
    pub fn try_reserve(&self, qty: i64) -> Result<i64, StockError> {
        if qty <= 0 {
            return Err(StockError::InvalidQuantity(qty));
        }

        let mut current = self.remaining.load(Ordering::Acquire);
        loop {
            if current < qty {
                return Err(StockError::SoldOut {
                    requested: qty,
                    available: current.max(0),
                });
            }
            let next = current - qty;
            match self.remaining.compare_exchange_weak(
                current,
                next,
                Ordering::AcqRel,
                Ordering::Acquire,
            ) {
                Ok(_) => return Ok(next),
                Err(actual) => current = actual,
            }
        }
    }
}
