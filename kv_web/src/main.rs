use actix_web::{HttpServer, App, web, Responder};
use fasthash::city;
use reqwest;

fn hello() -> impl Responder {
    "KVFinder Web"
}

fn get_id(tag_id: &String) -> Result<Option<String>, reqwest::Error> {
    let url = format!("http://0.0.0.0:8023/tag/{}", tag_id);
    let mut ids: Vec<String> = reqwest::get(url.as_str())?.json()?;
    //ids = vec!(String::from("1"),String::from("2"));
    Ok(ids.pop())
}

fn ask(id: web::Path<String>) -> impl Responder {
    let tag_id = id.into_inner();
    let queue_id = get_id(&tag_id);
    match queue_id {
        Ok(None) => format!("{} not found in job queue", tag_id),
        Ok(Some(id)) => format!("{} {}", tag_id, id),
        Err(e) => format!("{:?}", e),
    }
}

fn main() {
    let s = String::from("{data: atoms}");
    let h = city::hash64(&s);
    println!("{} {}", s, h);
    println!("Hello, world!");
    
    HttpServer::new(|| {
        App::new()
            .route("/", web::get().to(hello))
            .route("/{id}", web::get().to(ask))
    })
    .bind("127.0.0.1:8081")
    .expect("Cannot bind to port 8081")
    .run()
    .unwrap();
}

// get id (hash256)
// - assert id is valid (lenght?)
// - check if id is in ocypod queue (get status)
//   - possible status values (not found, queue, running, complete, fail)
// - if status complete -> return data (cavities) to client
// - if status running -> return "running"
// - if status queue -> return "position in queue"
// - if not found -> return "not found" (HTTP 404?)
// - if fail -> return "messages to log"


// post json (string)
// - create hash256 (id) from json
// - check if id is in ocypod queue (same as get id except)
// - if not found -> 
//   - validate json 
//   - submit to ocypod
//   - return status "created" with id hash256
