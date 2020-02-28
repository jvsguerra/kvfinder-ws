import json
import requests
import zlib
from time import sleep

def add_settings(job_input):
    job_input["settings"] = {}
    job_input["settings"]["modes"] = {
        "whole_protein_mode" : True,
        "box_mode" : False,
        "resolution_mode" : "Low",
        "surface_mode" : True,
        "kvp_mode" : False,
        "ligand_mode" : False,
    }

    job_input["settings"]["step_size"] = {"step_size": 0.0}

    job_input["settings"]["probes"] = {
        "probe_in" : 1.4,
        "probe_out" : 4.0,
    }

    job_input["settings"]["cutoffs"] = {
        "volume_cutoff" : 5.0,
        "ligand_cutoff" : 5.0,
        "removal_distance" : 2.4,
    }

    job_input["settings"]["visiblebox"] = {
        "p1" : {"x" : 0.00, "y" : 0.00, "z" : 0.00},
        "p2" : {"x" : 0.00, "y" : 0.00, "z" : 0.00},
        "p3" : {"x" : 0.00, "y" : 0.00, "z" : 0.00},
        "p4" : {"x" : 0.00, "y" : 0.00, "z" : 0.00},
    }

    job_input["settings"]["internalbox"] = {
        "p1" : {"x" : -4.00, "y" : -4.00, "z" : -4.00},
        "p2" : {"x" : 4.00, "y" : -4.00, "z" : -4.00},
        "p3" : {"x" : -4.00, "y" : 4.00, "z" : -4.00},
        "p4" : {"x" : -4.00, "y" : -4.00, "z" : 4.00},
    }

def add_pdb(job_input, pdb_fn, is_ligand=False):
    with open(pdb_fn) as f:
        pdb = f.readlines()
    if is_ligand:
        job_input["pdb_ligand"] = pdb
    else:
        job_input["pdb"] = pdb


def create_job_input(path_protein_pdb, path_ligand_pdb=None):
    job_input = {}
    add_settings(job_input)
    add_pdb(job_input, path_protein_pdb)
    if path_ligand_pdb == None:
        job_input["pdb_ligand"] = None
    else:
        add_pdb(job_input, path_ligand_pdb, is_ligand=True)
    return job_input

def send_job(server, job_input):
    r = requests.post(server + '/create', json=job_input)
    return r.json()['id']

def get_job(server, job_id):
    r = requests.get(server + '/' + job_id)
    if r.ok:
        results = r.json()
        if results['status'] == 'completed':
            return results
        else:
            print(results)
            return None
    else:
        print(r)
        return None

if __name__ == "__main__":
    job_input = create_job_input("./1FMO.pdb")
    # print(job_input)
    server = "http://localhost:8081"
    job_id = send_job(server, job_input)
    results = None
    while results == None:
        results = get_job(server, job_id)
        sleep(2)
    # pdb file 
    print(results['output']['pdb_kv'])
    # toml report
    print(results['output']['report'])
    # log
    print(results['output']['log'])
