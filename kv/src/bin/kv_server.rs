use kv;
use actix_web::{HttpServer, App, web};

fn main() {
    println!("KVFinder webserver started");
    
    HttpServer::new(|| {
        App::new()
            .data(web::JsonConfig::default().limit(1_000_000))
            .route("/", web::get().to(kv::webserver::hello))
            .route("/{id}", web::get().to(kv::webserver::ask))
            .route("/create", web::post().to(kv::webserver::create)) 
    })
    .bind("127.0.0.1:8081")
    .expect("Cannot bind to port 8081")
    .run()
    .unwrap();
}