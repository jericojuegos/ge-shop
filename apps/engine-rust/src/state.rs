use crate::domain::StockPool;
use std::collections::HashMap;
use std::sync::{Arc, RwLock};

#[derive(Clone, Default)]
pub struct AppState {
    pub pools: Arc<RwLock<HashMap<String, Arc<StockPool>>>>,
}

impl AppState {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn upsert_pool(&self, pool: StockPool) {
        let mut guard = self.pools.write().expect("pools lock poisoned");
        guard.insert(pool.sku_id().to_string(), Arc::new(pool));
    }

    pub fn get_pool(&self, sku_id: &str) -> Option<Arc<StockPool>> {
        let guard = self.pools.read().expect("pools lock poisoned");
        guard.get(sku_id).cloned()
    }
}
