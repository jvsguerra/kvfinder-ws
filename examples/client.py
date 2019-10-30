import json

class KVSettings(object):
    def __init__(self):
        self.modes = KVSettingsModes()

class KVSettingsModes(object):
    def __init__(self, whole_protein = True,
                 box= False,
                 resolution = "Low",
                 surface = True,
                 kvp = False,
                 ligand = False):
        self.whole_protein_mode = whole_protein
        self.box_mode = box
        self.resolution_mode = resolution
        self.surface_mode = surface
        self.kvp_mode = kvp
        self.ligand_mode = ligand

if __name__ == "__main__":
    settings = KVSettings()
    d = json.dumps(settings)
    print(d)