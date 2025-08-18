import json, numpy as np
from .tiles import LEGEND
def save_map_json(m, path:str):
    data = {"h": int(m.grid.shape[0]), "w": int(m.grid.shape[1]),
            "grid": m.grid.astype(int).tolist(), "legend": LEGEND}
    with open(path, "w") as f: json.dump(data, f)
