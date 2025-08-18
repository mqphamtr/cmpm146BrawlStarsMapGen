import numpy as np
import matplotlib.pyplot as plt
from map.map_repr import BSMap
from map.io_fmt import save_map_json

from fitness import evaluate_map_fitness  

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

    game_map = m.grid.tolist()  # convert numpy array -> list of lists
    fitness_score = evaluate_map_fitness(game_map)
    print("Fitness Score:", fitness_score)
