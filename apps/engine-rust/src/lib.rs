pub mod domain;
pub mod handlers;
pub mod state;

#[cfg(test)]
mod tests {
    use crate::domain::{Money, MoneyError, StockError, StockPool};
    use std::sync::atomic::{AtomicUsize, Ordering};
    use std::sync::Arc;
    use std::thread;

    #[test]
    fn test_money_integer_cents_and_clamped_discounts() {
        let price = Money::new(250_000).expect("valid money");
        let shipping = Money::new(15_000).expect("valid money");
        let total = price.checked_add(shipping).expect("no overflow");
        assert_eq!(total.cents(), 265_000);

        let after_voucher = price.apply_discount_clamped(50_000).expect("valid discount");
        assert_eq!(after_voucher.cents(), 200_000);

        let clamped_to_zero = price.apply_discount_clamped(999_999).expect("clamped discount");
        assert_eq!(clamped_to_zero.cents(), 0);

        assert_eq!(Money::new(-1), Err(MoneyError::NegativeAmount(-1)));
        assert_eq!(
            price.apply_discount_clamped(-10),
            Err(MoneyError::NegativeAmount(-10))
        );
    }

    #[test]
    fn test_stock_pool_sequential_and_error_invariants() {
        let pool = StockPool::new("sku-flash-01", Money::new(99_000).unwrap(), 5)
            .expect("valid stock pool");
        assert_eq!(pool.available(), 5);
        assert_eq!(pool.flash_price().cents(), 99_000);

        assert_eq!(pool.try_reserve(0), Err(StockError::InvalidQuantity(0)));
        assert_eq!(pool.try_reserve(-2), Err(StockError::InvalidQuantity(-2)));

        assert_eq!(pool.try_reserve(3), Ok(2));
        assert_eq!(pool.available(), 2);

        assert_eq!(
            pool.try_reserve(3),
            Err(StockError::SoldOut {
                requested: 3,
                available: 2
            })
        );
        assert_eq!(pool.available(), 2);
    }

    #[test]
    fn test_stock_pool_concurrent_contention_never_goes_negative() {
        let pool = Arc::new(
            StockPool::new("sku-flash-10", Money::new(100_000).unwrap(), 10)
                .expect("valid stock pool"),
        );
        let granted = Arc::new(AtomicUsize::new(0));
        let sold_out = Arc::new(AtomicUsize::new(0));

        let mut handles = Vec::with_capacity(200);
        for _ in 0..200 {
            let pool_ref = Arc::clone(&pool);
            let granted_ref = Arc::clone(&granted);
            let sold_out_ref = Arc::clone(&sold_out);
            handles.push(thread::spawn(move || match pool_ref.try_reserve(1) {
                Ok(_) => {
                    granted_ref.fetch_add(1, Ordering::Relaxed);
                }
                Err(StockError::SoldOut { .. }) => {
                    sold_out_ref.fetch_add(1, Ordering::Relaxed);
                }
                Err(other) => panic!("unexpected error: {:?}", other),
            }));
        }

        for h in handles {
            h.join().expect("worker thread panicked");
        }

        assert_eq!(granted.load(Ordering::SeqCst), 10);
        assert_eq!(sold_out.load(Ordering::SeqCst), 190);
        assert_eq!(pool.available(), 0);
    }
}
