import json
import requests
import zlib
from time import sleep

class KVClient:
    def __init__(self, server, port):
        self.server = "{}:{}".format(server, port)


    def run(self, kv_job):
        self._submit(kv_job)
        while kv_job.output == None:
            kv_job.output = self._get_results(kv_job)
            sleep(2)
        print("OK")

    def _submit(self, kv_job):
        r = requests.post(self.server + '/create', json=kv_job.input)
        if r.ok:
            kv_job.id = r.json()['id']
            return True
        else:
            print("Debug:", r)
            return False

    def _get_results(self, kv_job):
        r = requests.get(self.server + '/' + kv_job.id)
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


class KVJob:
    def __init__(self, path_protein_pdb, path_ligand_pdb=None):
        self.id = None
        self.input = {}
        self.output = None 
        self._add_pdb(path_protein_pdb)
        if path_ligand_pdb != None:
            self._add_path(path_ligand_pdb, is_ligand=True)
        self._default_settings()

    @property
    def kv_pdb(self):
        if self.output == None:
            return None
        else:
            return self.output["output"]["pdb_kv"]

    @property
    def report(self):
        if self.output == None:
            return None
        else:
            return self.output["output"]["report"]

    @property
    def log(self):
        if self.output == None:
            return None
        else:
            return self.output["output"]["log"]

    def _add_pdb(self, pdb_fn, is_ligand=False):
        with open(pdb_fn) as f:
            pdb = f.readlines()
        if is_ligand:
            self.input["pdb_ligand"] = pdb
        else:
            self.input["pdb"] = pdb

    def _default_settings(self):
        self.input["settings"] = {}
        self.input["settings"]["modes"] = {
            "whole_protein_mode" : True,
            "box_mode" : False,
            "resolution_mode" : "Low",
            "surface_mode" : True,
            "kvp_mode" : False,
            "ligand_mode" : False,
        }
        self.input["settings"]["step_size"] = {"step_size": 0.0}
        self.input["settings"]["probes"] = {
            "probe_in" : 1.4,
            "probe_out" : 4.0,
        }
        self.input["settings"]["cutoffs"] = {
            "volume_cutoff" : 5.0,
            "ligand_cutoff" : 5.0,
            "removal_distance" : 2.4,
        }
        self.input["settings"]["visiblebox"] = {
            "p1" : {"x" : 0.00, "y" : 0.00, "z" : 0.00},
            "p2" : {"x" : 0.00, "y" : 0.00, "z" : 0.00},
            "p3" : {"x" : 0.00, "y" : 0.00, "z" : 0.00},
            "p4" : {"x" : 0.00, "y" : 0.00, "z" : 0.00},
        }
        self.input["settings"]["internalbox"] = {
            "p1" : {"x" : -4.00, "y" : -4.00, "z" : -4.00},
            "p2" : {"x" : 4.00, "y" : -4.00, "z" : -4.00},
            "p3" : {"x" : -4.00, "y" : 4.00, "z" : -4.00},
            "p4" : {"x" : -4.00, "y" : -4.00, "z" : 4.00},
        }


    

if __name__ == "__main__":
    kv = KVClient("http://localhost", "8081")
    job = KVJob("./1FMO.pdb")
    kv.run(job)
    # print(job.output)
    print(json.dumps(job.output, indent=2))