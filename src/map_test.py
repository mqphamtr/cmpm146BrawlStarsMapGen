import numpy as np
import matplotlib.pyplot as plt
from map.map_repr import BSMap
from map.io_fmt import save_map_json

if __name__ == "__main__":
    np.random.seed(123)
    m = BSMap.random()

    print(m.to_ascii())                             #print to terminal

    plt.imshow(m.grid, interpolation="nearest")     #print to window/matplotlib
    plt.title("Brawl Stars Map (tile ids)")
    plt.axis("off")
    plt.show()

    save_map_json(m, "sample_map.json")             #save as .json for unity
    print("Saved sample_map.json")
