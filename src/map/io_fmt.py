import json, numpy as np
from .tiles import LEGEND
from .map_repr import BSMap

def save_map_json(m, path:str):
    data = {"h": int(m.grid.shape[0]), "w": int(m.grid.shape[1]),
            "grid": m.grid.astype(int).tolist(), "legend": LEGEND}
    with open(path, "w") as f: json.dump(data, f)

def save_map_txt(m, path:str):
    with open(path, "w", newline="\n") as f:
        for row in m.grid:
            f.write(" ".join(str(int(x)) for x in row) + "\n")