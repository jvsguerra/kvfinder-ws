mod kv { 
    use serde::{Deserialize, Serialize};

    #[derive(Serialize, Deserialize, Debug)]
    struct KVParameters {
        title: String,
        files_path: KVFilesPath,
        settings: KVSettings,
    }

    #[derive(Serialize, Deserialize, Debug)]
    struct KVFilesPath {
        dictionary: String,
        pdb: String,
        output: String,
        base_name: String,
        ligand: String,
    }

    #[derive(Serialize, Deserialize, Debug, Clone)]
    #[serde(deny_unknown_fields)]
    struct KVSettings {
        modes: KVSModes,
        step_size: KVSStepSize,
        probes: KVSProbes,
        cutoffs: KVSCutoffs,
        visiblebox: KVSVisiblebox,
        internalbox: KVSInternalbox,
    }

    #[derive(Serialize, Deserialize, Debug, Clone)]
    #[serde(deny_unknown_fields)]
    struct KVSModes {
        whole_protein_mode: bool,
        box_mode: bool,
        resolution_mode: KVSResolution, 
        surface_mode: bool,
        kvp_mode: bool,
        ligand_mode: bool,
    }

    #[derive(Serialize, Deserialize, PartialEq, Debug, Clone)]
    #[serde(deny_unknown_fields)]
    enum KVSResolution {
        Low,
        Medium,
        High,
        Off,
    }

    #[derive(Serialize, Deserialize, Debug, Clone)]
    #[serde(deny_unknown_fields)]
    struct KVSStepSize {
        step_size: f64,
    }

    #[derive(Serialize, Deserialize, Debug, Clone)]
    #[serde(deny_unknown_fields)]
    struct KVSProbes {
        probe_in: f64,
        probe_out: f64,
    }

    #[derive(Serialize, Deserialize, Debug, Clone)]
    #[serde(deny_unknown_fields)]
    struct KVSCutoffs {
        volume_cutoff: f64,
        ligand_cutoff: f64,
        removal_distance: f64,
    }

    #[derive(Serialize, Deserialize, Debug, Clone)]
    #[serde(deny_unknown_fields)]
    struct KVSVisiblebox {
        p1: KVSBoxPoint,
        p2: KVSBoxPoint,
        p3: KVSBoxPoint,
        p4: KVSBoxPoint,
    }

    #[derive(Serialize, Deserialize, Debug, Clone)]
    #[serde(deny_unknown_fields)]
    struct KVSInternalbox {
        p1: KVSBoxPoint,
        p2: KVSBoxPoint,
        p3: KVSBoxPoint,
        p4: KVSBoxPoint,

    }

    #[derive(Serialize, Deserialize, Debug, Clone)]
    #[serde(deny_unknown_fields)]
    struct KVSBoxPoint {
        x: f64, 
        y: f64,
        z: f64,
    }

    struct PdbBoundaries {
        x_min: f64,
        x_max: f64,
        y_min: f64,
        y_max: f64,
        z_min: f64,
        z_max: f64,
    }

    #[derive(Serialize, Deserialize, Debug)]
    #[serde(deny_unknown_fields)]
    pub struct Input {
        settings: KVSettings,
        pdb: Vec<String>,
        pdb_ligand: Option<Vec<String>>,
    }

    impl Input {

        fn check(&self) -> Result<(), &str> {
            // Compare Whole protein and Box modes
            if self.settings.modes.whole_protein_mode == self.settings.modes.box_mode {
                return Err("Invalid parameters file! Whole protein and box modes cannot be equal!");
            }
            // Compare resolution mode
            if self.settings.modes.resolution_mode != KVSResolution::Low {
               return Err("Invalid parameters file! Resolution mode is restricted to Low option on this web service!");
            }
            // Probe In
            if self.settings.probes.probe_in < 0.0 || self.settings.probes.probe_in > 5.0 {
                return Err("Invalid parameters file! Probe In must be between 0 and 5!");
            }
            // Probe Out
            if self.settings.probes.probe_out < 0.0 || self.settings.probes.probe_out > 50.0 {
                return Err("Invalid parameters file! Probe Out must be between 0 and 50!");
            }
            // Compare probes
            if self.settings.probes.probe_out < self.settings.probes.probe_in {
                return Err("Invalid parameters file! Probe Out must be greater than Probe In!");
            }
            // Removal distance
            if self.settings.cutoffs.removal_distance < 0.0 || self.settings.cutoffs.removal_distance > 10.0 {
                return Err("Invalid parameters file! Removal distance must be between 0 and 10!");
            }
            // Volume Cutoff
            if self.settings.cutoffs.volume_cutoff < 0.0 {
                return Err("Invalid parameters file! Volume cutoff must be greater than 0!");
            }    
            // Cavity representation
            if self.settings.modes.kvp_mode {
                return Err("Invalid parameters file! Cavity Representation (kvp_mode) must be false on this webservice!");
            }
            // Ligand mode and pdb
            if self.settings.modes.ligand_mode && self.pdb_ligand == None {
                 return Err("Invalid parameters file! A ligand must be provided when Ligand mode is set to true!");
            } else if !self.settings.modes.ligand_mode && self.pdb_ligand != None {
                    return Err("Invalid parameters file! The Ligand mode must be set to true when providing a ligand!");
            }
            // Ligand Cutoff
            if self.settings.cutoffs.ligand_cutoff <= 0.0 {
                return Err("Invalid parameters file! Ligand cutoff must be greater than 0!");
            }
            // Box coordinates
            if self.settings.modes.box_mode {
                // 1) box[internal] > box[visible]
                let x = vec![self.settings.internalbox.p1.x, self.settings.internalbox.p2.x, self.settings.internalbox.p3.x, self.settings.internalbox.p4.x];
                let y = vec![self.settings.internalbox.p1.y, self.settings.internalbox.p2.y, self.settings.internalbox.p3.y, self.settings.internalbox.p4.y];
                let z = vec![self.settings.internalbox.p1.z, self.settings.internalbox.p2.z, self.settings.internalbox.p3.z, self.settings.internalbox.p4.z];
                let xmin = x.iter().fold(f64::INFINITY, |a, &b| a.min(b));
                let xmax = x.iter().fold(f64::INFINITY, |a, &b| a.max(b));
                let ymin = y.iter().fold(f64::INFINITY, |a, &b| a.min(b));
                let ymax = y.iter().fold(f64::INFINITY, |a, &b| a.max(b));
                let zmin = z.iter().fold(f64::INFINITY, |a, &b| a.min(b));
                let zmax = z.iter().fold(f64::INFINITY, |a, &b| a.max(b));
                // P1
                if (self.settings.visiblebox.p1.x < xmin || self.settings.visiblebox.p1.x > xmax) || (self.settings.visiblebox.p1.y < ymin || self.settings.visiblebox.p1.y > ymax) || (self.settings.visiblebox.p1.z < zmin || self.settings.visiblebox.p1.z > zmax) {
                    return Err("Invalid parameters file! Inconsistent box coordinates!")
                }
                // P2
                if (self.settings.visiblebox.p2.x < xmin || self.settings.visiblebox.p2.x > xmax) || (self.settings.visiblebox.p2.y < ymin || self.settings.visiblebox.p2.y > ymax) || (self.settings.visiblebox.p2.z < zmin || self.settings.visiblebox.p2.z > zmax) {
                    return Err("Invalid parameters file! Inconsistent box coordinates!")
                }
                // P3
                if (self.settings.visiblebox.p3.x < xmin || self.settings.visiblebox.p3.x > xmax) || (self.settings.visiblebox.p3.y < ymin || self.settings.visiblebox.p3.y > ymax) || (self.settings.visiblebox.p3.z < zmin || self.settings.visiblebox.p3.z > zmax) {
                    return Err("Invalid parameters file! Inconsistent box coordinates!")
                }
                // P4
                if (self.settings.visiblebox.p4.x < xmin || self.settings.visiblebox.p4.x > xmax) || (self.settings.visiblebox.p4.y < ymin || self.settings.visiblebox.p4.y > ymax) || (self.settings.visiblebox.p4.z < zmin || self.settings.visiblebox.p4.z > zmax) {
                    return Err("Invalid parameters file! Inconsistent box coordinates!")
                }
                // 2) box[internal] < pdb_boundaries[pdb] +- ( probe_out + 20.0 A )
                let pdb_boundaries = self.get_pdb_boundaries();
                // P1
                if (self.settings.internalbox.p1.x < pdb_boundaries.x_min || self.settings.internalbox.p1.x > pdb_boundaries.x_max) || (self.settings.internalbox.p1.y < pdb_boundaries.y_min || self.settings.internalbox.p1.y > pdb_boundaries.y_max) || (self.settings.internalbox.p1.z < pdb_boundaries.z_min || self.settings.internalbox.p1.z > pdb_boundaries.z_max) {
                    return Err("Invalid parameters file! Inconsistent box coordinates!")
                }
                // P2
                if (self.settings.internalbox.p2.x < pdb_boundaries.x_min || self.settings.internalbox.p2.x > pdb_boundaries.x_max) || (self.settings.internalbox.p2.y < pdb_boundaries.y_min || self.settings.internalbox.p2.y > pdb_boundaries.y_max) || (self.settings.internalbox.p2.z < pdb_boundaries.z_min || self.settings.internalbox.p2.z > pdb_boundaries.z_max) {
                    return Err("Invalid parameters file! Inconsistent box coordinates!")
                }
                // P3
                if (self.settings.internalbox.p3.x < pdb_boundaries.x_min || self.settings.internalbox.p3.x > pdb_boundaries.x_max) || (self.settings.internalbox.p3.y < pdb_boundaries.y_min || self.settings.internalbox.p3.y > pdb_boundaries.y_max) || (self.settings.internalbox.p3.z < pdb_boundaries.z_min || self.settings.internalbox.p3.z > pdb_boundaries.z_max) {
                    return Err("Invalid parameters file! Inconsistent box coordinates!")
                }
                // P4
                if (self.settings.internalbox.p4.x < pdb_boundaries.x_min || self.settings.internalbox.p4.x > xmax) || (self.settings.internalbox.p4.y < pdb_boundaries.y_min || self.settings.internalbox.p4.y > ymax) || (self.settings.internalbox.p4.z < pdb_boundaries.z_min || self.settings.internalbox.p4.z > zmax) {
                    return Err("Invalid parameters file! Inconsistent box coordinates!")
                }
            }
            // Return Ok (All parameters are acceptable)
            Ok(())
        }

        fn get_pdb_boundaries(&self) -> PdbBoundaries {
            let mut x_min : f64 = 99999.9;
            let mut y_min : f64 = 99999.9;
            let mut z_min : f64 = 99999.9;
            let mut x_max : f64 = -99999.9;
            let mut y_max : f64 = -99999.9;
            let mut z_max : f64 = -99999.9;

            let mut atoms = IntoIterator::into_iter(&self.pdb); // strings is moved here
            while let Some(atom) = atoms.next() { // next() moves a string out of the iter
                if atom.contains("ATOM") || atom.contains("HETATM") {
                    let xs : String = atom[30..38].chars().filter(|c| !c.is_whitespace()).collect();
                    let ys : String = atom[38..46].chars().filter(|c| !c.is_whitespace()).collect();
                    let zs : String = atom[46..54].chars().filter(|c| !c.is_whitespace()).collect();
                    let x : f64 = xs.parse().unwrap();
                    let y : f64 = ys.parse().unwrap();
                    let z : f64 = zs.parse().unwrap();
                    if x_min > x {
                        x_min = x;
                    }
                    if x_max < x {
                        x_max = x;
                    }
                    if y_min > y {
                        y_min = y;
                    }
                    if y_max < y {
                        y_max = y;
                    }
                    if z_min > z {
                        z_min = z;
                    }
                    if z_max < z {
                        z_max = z;
                    }

                }
            }
            PdbBoundaries {
                x_min : x_min - self.settings.probes.probe_out - 20.0,
                x_max : x_max + self.settings.probes.probe_out + 20.0,
                y_min : y_min - self.settings.probes.probe_out - 20.0,
                y_max : y_max + self.settings.probes.probe_out + 20.0,
                z_min : z_min - self.settings.probes.probe_out - 20.0,
                z_max : z_max + self.settings.probes.probe_out + 20.0,
            }
        }
    }

    #[derive(Serialize, Deserialize, Debug, Clone)]
    pub struct Output {
        pdb_kv: String,
        report: String,
        log: String,
    }

    #[derive(Serialize, Deserialize)]
    struct Data {
        tags: [String;1],
        input: Input,
    }

    pub mod worker {
        use std::io;
        use std::io::Write;
        use reqwest;
        use std::process::Command;
        use std::fs;
        use toml;
        use serde::{Deserialize, Serialize};
        use std::path::Path;
        use std::fs::{File,create_dir};
        use super::{Input, Output};

        #[derive(Serialize, Deserialize, Debug)]
        pub struct JobInput {
            pub id: u32,
            input: Input,
        }

        #[derive(Serialize, Deserialize, Debug, Clone)]
        struct JobOutput {
            status: String,
            output: Output,
        }

        pub struct Config {
            pub kv_path: String,
            pub job_path: String,
        }

        impl JobInput {
            fn save(&self, config: &Config) -> Result<(), io::Error> {
                self.input.save(self.id, &config)?;
                Ok(())
            }
    
            fn run(&self, config: &Config) -> Result<Output, io::Error> {
                let kvfinder = Command::new(format!("{}/parKVFinder", config.kv_path))
                                    .current_dir(format!("{}/{}", config.job_path, self.id))
                                    .arg("-p")
                                    .arg("params.toml")
                                    .status()
                                    .expect("failed to execute KVFinder process");
                println!("process exited with: {}", kvfinder);
                if kvfinder.success() {
                    let output = Output { 
                        pdb_kv:  fs::read_to_string(format!("{}/{}/KV_Files/KVFinderWeb/KVFinderWeb.KVFinder.output.pdb", config.job_path, self.id))?,
                        report:  fs::read_to_string(format!("{}/{}/KV_Files/KVFinderWeb/KVFinderWeb.KVFinder.results.toml", config.job_path, self.id))?, 
                        log: fs::read_to_string(format!("{}/{}/KV_Files/KVFinder.log", config.job_path, self.id))?, 
                    };
                    println!("KVFinder OK");
                    return Ok(output);
                } else {
                    return Err(io::Error::new(io::ErrorKind::Other, "oh no! check if variable KVFinder_PATH was set"));
                }
            }
        }
   
        impl Input {
            fn save(&self, id: u32, config: &Config) -> Result<(), io::Error> {
                let dir = format!("{}/{}", config.job_path, id);
                match create_dir(&dir) {
                    Err(err) => Err(err),
                    Ok(_) => {
                        self.save_parameters(&dir, &config)?;
                        self.save_pdb(&dir)?;
                        if let Some(_) = self.pdb_ligand {
                            self.save_pdb_ligand(&dir)?;
                        }
                        Ok(())
                    },
                }
            }
    
            fn save_parameters(&self, dir: &str, config: &Config) -> Result<(), io::Error> {
                let params = super::KVParameters{
                    title: String::from("KVFinder-worker parameters"),
                    files_path: super::KVFilesPath{
                        dictionary: String::from(format!("{}/dictionary", config.kv_path)),
                        pdb: String::from("./protein.pdb"),
                        ligand: String::from("./ligand.pdb"),
                        output: String::from("./"),
                        base_name: String::from("KVFinderWeb"),
                    },
                    settings: self.settings.clone(),
                };
                let toml_parameters = toml::to_string(&params);
                let filename = format!("{}/params.toml", dir);
                let path = Path::new(&filename);
                let mut file = File::create(path)?;
                if let Ok(p) = toml_parameters {
                    writeln!(file, "{}", p)?;
                }
                Ok(())
            }
    
            fn save_pdb(&self, dir: &str) -> Result<(), io::Error> {
                let filename = format!("{}/protein.pdb", dir);
                let path = Path::new(&filename);
                let mut file = File::create(path)?;
                writeln!(file, "{}", self.pdb.join(""))?;
                Ok(())
            }
    
            fn save_pdb_ligand(&self, dir: &str) -> Result<(), io::Error> {
                let filename = format!("{}/ligand.pdb", dir);
                let path = Path::new(&filename); 
                let mut file = File::create(&path)?;
                if let Some(pdb_ligand) = &self.pdb_ligand {
                    writeln!(file, "{}", pdb_ligand.join(""))?;
                }
                Ok(())
            }
        }

        pub fn get_job() -> Result<JobInput, reqwest::Error> {
            // let j: JobInput = reqwest::get("http://0.0.0.0:8023/queue/kvfinder/job")?.json()?;
            let j: JobInput = reqwest::get("http://ocypod:8023/queue/kvfinder/job")?.json()?;
            Ok(j)
        }

        pub fn process(job: JobInput, config: &Config) -> Result<Output, io::Error> {
            job.save(&config)?;
            let output = job.run(&config); 
            output
        }

        pub fn submit_result(id: u32, output: Output) -> Result<u32, reqwest::Error> {
            let client = reqwest::Client::new();
            // let url = format!("http://0.0.0.0:8023/job/{}", id);
            let url = format!("http://ocypod:8023/job/{}", id);
            let data = JobOutput {
                status: String::from("completed"),
                output,
            };
            let _result = client.patch(url.as_str())
                .json(&data)
                .send()?;
            Ok(id)
        }
    }

    pub mod webserver {
        use actix_web::{web, Responder, HttpResponse};
        use reqwest;
        use serde_json;
        use serde_json::json;
        use fasthash::city;
        use serde::{Deserialize, Serialize};
        use super::{Input, Output, Data};

        #[derive(Serialize, Deserialize)]
        struct Job {
            #[serde(default)]
            id: String,     // this id is the same as tag_id (NOT queue_id)
            status: String,
            output: Option<Output>,
            created_at: String,
            started_at: Option<String>,
            ended_at: Option<String>, 
            expires_after: String,
        }


        #[derive(Serialize, Deserialize)]
        struct QueueConfig<'a> {
            timeout: &'a str,
            expires_after: &'a str,
            retries: i32,
        }
        

        pub fn hello() -> impl Responder {
            "KVFinder Web"
        }


        pub fn create_ocypod_queue(queue_name: &str, timeout: &str, expires_after: &str, retries: i32) {
            let client = reqwest::Client::new();
            let queue_url = format!("http://ocypod:8023/queue/{}", queue_name);
            let queue_config = QueueConfig { timeout, expires_after, retries };
            let _response = client.put(&queue_url)
                .json(&queue_config)
                .send();
            // match _response {
            //     Ok(_) => HttpResponse::Ok().json(json!({"id":data.tags[0]})),
            //     Err(e) => HttpResponse::InternalServerError().body(format!("{:?}", e)),
            // }
        }
        
        fn get_queue_id(tag_id: &String) -> Result<Option<u32>, reqwest::Error> {
            // let url = format!("http://0.0.0.0:8023/tag/{}", tag_id);
            let url = format!("http://ocypod:8023/tag/{}", tag_id);

            // ids because in theory could be more than one with the same tag, BUT if this happen there is an error 
            // if tag_id (hash64) not found in queue Ok(None)
            // if request fail return Err (possible problem in queue server)
            let mut ids: Vec<u32> = reqwest::get(url.as_str())?.json()?; 
            // pop returns last id (should have only one or zero) or None
            Ok(ids.pop())
        }
        
        fn get_job(tag_id: String) -> Result<Option<Job>, reqwest::Error> {
            let queue_id = get_queue_id(&tag_id);
            let job = |queue_id| {
                // let url = format!("http://0.0.0.0:8023/job/{}?fields=status,output,created_at,started_at,ended_at,expires_after", queue_id);
                let url = format!("http://ocypod:8023/job/{}?fields=status,output,created_at,started_at,ended_at,expires_after", queue_id);
                let mut j: Job = reqwest::get(url.as_str())?.json()?;
                j.id = tag_id;
                Ok(Some(j))
            };
         
            match queue_id {
                    Err(e) => Err(e),
                    // if queue_id is None (tag_id not found) 
                    Ok(None) => return Ok(None),
                    // return job data in json
                    Ok(Some(queue_id)) => return job(queue_id), 
            }
        }
        
        pub fn ask(id: web::Path<String>) -> impl Responder {
            let tag_id = id.into_inner();
            let job = get_job(tag_id);
            match job {
                Err(e) => HttpResponse::InternalServerError().body(format!("{:?}", e)),
                Ok(None) => HttpResponse::NotFound().finish(),
                Ok(Some(j)) => HttpResponse::Ok().json(j),
            }
        }

        pub fn create(job_input: web::Json<Input>) -> impl Responder {
            // json input values to inp
            let input = job_input.into_inner();
            if let Err(e) = &input.check() {
                return HttpResponse::BadRequest().body(format!("{:?}", e));
            }
            let data = Data {
                // create a tag using function hash64 applied to input (unique value per input)
                tags: [city::hash64(serde_json::to_string(&input).unwrap()).to_string()],
                input,
            };
            let create_job = || {
                let client = reqwest::Client::new();
                let response = client.post("http://ocypod:8023/queue/kvfinder/job")
                    .json(&data)
                    .send();
                match response {
                    Ok(_) => HttpResponse::Ok().json(json!({"id":data.tags[0]})),
                    Err(e) => HttpResponse::InternalServerError().body(format!("{:?}", e)),
                }
            };
            let job = get_job(data.tags[0].clone());
            match job {
                // if err, problem in queue server
                Err(e) => HttpResponse::InternalServerError().body(format!("{:?}", e)),
                // if job with this tag is in queue, return job 
                Ok(Some(j)) => HttpResponse::Ok().json(j),
                // if job with this tag is not found on queue, create job
                Ok(None) => create_job(), //format!("{} created", tag_id),
            }
        }

    }
}

pub use crate::kv::worker;
pub use crate::kv::webserver;    
