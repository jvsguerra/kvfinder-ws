import json
import requests
import zlib

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
        "bP1" : {"bX1" : 0.00, "bY1" : 0.00, "bZ1" : 0.00},
        "bP2" : {"bX2" : 0.00, "bY2" : 0.00, "bZ2" : 0.00},
        "bP3" : {"bX3" : 0.00, "bY3" : 0.00, "bZ3" : 0.00},
        "bP4" : {"bX4" : 0.00, "bY4" : 0.00, "bZ4" : 0.00},
    }

    job_input["settings"]["internalbox"] = {
        "P1" : {"X1" : -4.00, "Y1" : -4.00, "Z1" : -4.00}
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
    # headers = {'Content-Type': 'application/json', 'Content-Encoding': 'gzip'}
    # job_input_json = bytes(json.dumps(job_input), 'utf8')
    r = requests.post(server + '/create', json=job_input)
    # print(job_input)
    # exit()
    # print(r.json()['id'])
    print(r, r.text)
    return r.json()['id']

def get_job(server, job_id):
    r = requests.get(server + '/' + job_id)
    if r.ok:
        print(r.json())
        return r.json()
    else:
        print(r)
        return None

if __name__ == "__main__":
    job_input = create_job_input("./1FMO.pdb")
    # job_input = {'f1': 'from-python-client', 'f2': 7, 'f3': 13}
    # print(job_input)
    server = "http://localhost:8081"
    job_id = send_job(server, job_input)
    get_job(server, job_id)
