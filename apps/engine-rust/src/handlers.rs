use crate::state::AppState;
use axum::{extract::State, routing::get, Json, Router};
use serde::Serialize;

#[derive(Serialize)]
pub struct HealthResponse {
    pub status: &'static str,
    pub service: &'static str,
    pub money_unit: &'static str,
}

pub async fn health_handler(State(_state): State<AppState>) -> Json<HealthResponse> {
    Json(HealthResponse {
        status: "ok",
        service: "ge-shop-engine-rust",
        money_unit: "cents_i64",
    })
}

pub fn build_router(state: AppState) -> Router {
    Router::new()
        .route("/health", get(health_handler))
        .with_state(state)
}
