use std::{thread,time};
use reqwest;
use serde::{Deserialize, Serialize};
use serde_json;

#[derive(Serialize, Deserialize, Debug)]
struct JobInput {
    id: u32,
    input: Input,
}

#[derive(Serialize, Deserialize, Debug)]
struct Input {
    f1: String,
    f2: i32,
    f3: i32,
}

#[derive(Serialize, Deserialize, Debug)]
struct JobOutput {
    status: String,
    output: Output,
}

#[derive(Serialize, Deserialize, Debug)]
struct Output {
    sum: i32,
    product: i32,
}

fn submit_result(id: u32, output: Output) -> Result<u32, reqwest::Error> {
    let client = reqwest::Client::new();
    let url = format!("http://0.0.0.0:8023/job/{}", id);
    let data = JobOutput {
        status: String::from("completed"),
        output: output,
    };
    let result = client.patch(url.as_str())
        .json(&data)
        .send()?;
    Ok(id)
}

fn process(job: JobInput) -> Result<u32, reqwest::Error> {
    let output = Output {
        sum: job.input.f2 + job.input.f3,
        product: job.input.f2 * job.input.f3,
    };
    submit_result(job.id, output)
}

fn get_job() -> Result<JobInput, reqwest::Error> {
    let j: JobInput = reqwest::get("http://0.0.0.0:8023/queue/dev/job")?.json()?;
    Ok(j)
}

fn main() {
    println!("Hello, world!");
    loop {
        let r = get_job();
        match r {
            Ok(j) => {
                match process(j) {
                    Ok(id) => println!("Completed id={}", id),
                    Err(e) => println!("Error during processing: {}", e),
                }
            },
            Err(e) => { 
                println!("{}", e);
                thread::sleep(time::Duration::from_secs(5));
            },
        }
    }
}
