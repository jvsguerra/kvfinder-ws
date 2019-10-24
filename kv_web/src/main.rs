use actix_web::{HttpServer, App, web, Responder};
use fasthash::city;
use reqwest;
use serde::{Deserialize, Serialize};
use serde_json;

#[derive(Serialize, Deserialize)]
struct Job {
    #[serde(default)]
    id: String,     // this id is the same as tag_id (NOT queue_id)
    status: String,
    output: Option<String>,
    created_at: String,
    started_at: Option<String>,
    ended_at: Option<String>, 
    expires_after: String,
}

fn hello() -> impl Responder {
    "KVFinder Web"
}

fn get_queue_id(tag_id: &String) -> Result<Option<u32>, reqwest::Error> {
    let url = format!("http://0.0.0.0:8023/tag/{}", tag_id);
    // ids because in theory could be more than one with the same tag, BUT if this happen there is an error 
    let mut ids: Vec<u32> = reqwest::get(url.as_str())?.json()?; 
        //ids = vec!(String::from("1"),String::from("2"));
    Ok(ids.pop())
}

fn get_job(tag_id: String) -> Result<Option<Job>, reqwest::Error> {
    let queue_id = get_queue_id(&tag_id);
    let job = |queue_id| {
        let url = format!("http://0.0.0.0:8023/job/{}?fields=status,output,created_at,started_at,ended_at,expires_after", queue_id);
        let mut j: Job = reqwest::get(url.as_str())?.json()?;
        j.id = tag_id;
        Ok(Some(j))
    };
 
    match queue_id {
            Err(e) => Err(e),
            Ok(None) => return Ok(None),
            Ok(Some(queue_id)) => return job(queue_id), 
    }
}

fn ask(id: web::Path<String>) -> impl Responder {
    let tag_id = id.into_inner();
    let job = get_job(tag_id);
    match job {
        Err(e) => format!("{:?}", e),
        Ok(None) => format!("not found in job queue"),
        Ok(Some(j)) => format!("{}", serde_json::to_string(&j).unwrap()),
    }
}

fn create() {}

fn main() {
    let s = String::from("{data: atoms}");
    let h = city::hash64(&s);
    println!("{} {}", s, h);
    println!("Hello, world!");
    
    HttpServer::new(|| {
        App::new()
            .route("/", web::get().to(hello))
            .route("/{id}", web::get().to(ask))
            .route("/create", web::post().to(create))
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
