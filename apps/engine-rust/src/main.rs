use ge_shop_engine_rust::handlers::build_router;
use ge_shop_engine_rust::state::AppState;
use tokio::net::TcpListener;

#[tokio::main]
async fn main() {
    let state = AppState::new();
    let app = build_router(state);
    let listener = TcpListener::bind("127.0.0.1:8081")
        .await
        .expect("failed to bind 127.0.0.1:8081");
    axum::serve(listener, app)
        .await
        .expect("axum server error");
}
