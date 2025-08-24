import copy
import random
from fitness import (
    evaluate_map_fitness, WALKABLE, WALL, WATER, COVER, BOX, SPAWN, BUSH, get_positions
)

class BrawlStarsMap:
    def __init__(self, size=(60, 60)):
        self.rows, self.cols = size
        self.map = [[WALKABLE for _ in range(self.cols)] for _ in range(self.rows)]
        self.fitness = None

    @classmethod
    def random_map(cls, rng, max_tries=20):
        for _ in range(max_tries):
            m = cls()
            # place spawns -> boxes -> obstacles -> bushes
            for x, y in m._generate_spawn_points(rng):
                m.map[y][x] = SPAWN
            m._place_boxes(rng, rng.randint(20, 35))
            m._add_walls(rng)
            m._add_water(rng)
            m._add_cover(rng)
            m._add_bushes(rng)
            if evaluate_map_fitness(m.map) > 0:
                return m
        return m

    def _generate_spawn_points(self, rng):
        spawns = [(5, 5), (self.cols - 6, 5), (5, self.rows - 6), (self.cols - 6, self.rows - 6)]
        cx, cy = self.cols // 2, self.rows // 2
        attempts = 0
        while len(spawns) < 10 and attempts < 500:
            x = rng.randint(cx - 25, cx + 25)
            y = rng.randint(cy - 25, cy + 25)
            if self._valid_spawn_position((x, y), spawns):
                spawns.append((x, y))
            attempts += 1
        return spawns

    def _valid_spawn_position(self, new_pos, existing):
        x, y = new_pos
        if x < 0 or x >= self.cols or y < 0 or y >= self.rows:
            return False
        for ex, ey in existing:
            if abs(ex - x) + abs(ey - y) < 18:  # Manhattan distance
                return False
        return True

    def _place_boxes(self, rng, count):
        cx, cy = self.cols // 2, self.rows // 2
        placed = 0
        center_boxes = max(8, count // 4)
        for _ in range(center_boxes):
            x = rng.randint(cx - 8, cx + 8)
            y = rng.randint(cy - 8, cy + 8)
            if self.map[y][x] == WALKABLE:
                self.map[y][x] = BOX
                placed += 1
        while placed < count:
            x = rng.randint(0, self.cols - 1)
            y = rng.randint(0, self.rows - 1)
            if self.map[y][x] == WALKABLE:
                self.map[y][x] = BOX
                placed += 1

    def _add_walls(self, rng):
        target = int(self.rows * self.cols * 0.20)
        obstacles = [WALL]
        placed = 0
        while placed < target:
            x = rng.randint(0, self.cols - 1)
            y = rng.randint(0, self.rows - 1)
            if self.map[y][x] == WALKABLE:
                self.map[y][x] = rng.choice(obstacles)
                placed += 1
    
    def _add_water(self, rng):
        target = int(self.rows * self.cols * 0.10)
        obstacles = [WATER]
        placed = 0
        while placed < target:
            x = rng.randint(0, self.cols - 1)
            y = rng.randint(0, self.rows - 1)
            if self.map[y][x] == WALKABLE:
                self.map[y][x] = rng.choice(obstacles)
                placed += 1

    def _add_cover(self, rng):
        target = int(self.rows * self.cols * 0.05)
        obstacles = [COVER]
        placed = 0
        while placed < target:
            x = rng.randint(0, self.cols - 1)
            y = rng.randint(0, self.rows - 1)
            if self.map[y][x] == WALKABLE:
                self.map[y][x] = rng.choice(obstacles)
                placed += 1

    def _add_bushes(self, rng):
        target = int(self.rows * self.cols * 0.10)
        placed = 0
        while placed < target:
            x = rng.randint(0, self.cols - 1)
            y = rng.randint(0, self.rows - 1)
            if self.map[y][x] == WALKABLE:
                self.map[y][x] = BUSH
                placed += 1

    def mutate(self, rng):
        mutation = rng.choice(['swap', 'add_tile', 'remove_tile'])

        if mutation == 'swap':
            for _ in range(10):
                x1, y1 = rng.randint(0, self.cols - 1), rng.randint(0, self.rows - 1)
                x2, y2 = rng.randint(0, self.cols - 1), rng.randint(0, self.rows - 1)
                if self.map[y1][x1] != SPAWN and self.map[y2][x2] != SPAWN:
                    self.map[y1][x1], self.map[y2][x2] = self.map[y2][x2], self.map[y1][x1]
                    break
        elif mutation == 'add_tile':
            x, y = rng.randint(0, self.cols - 1), rng.randint(0, self.rows - 1)
            if self.map[y][x] == WALKABLE:
                self.map[y][x] = rng.choice([WALL, WATER, COVER, BUSH, BOX])
        elif mutation == 'remove_tile':
            x, y = rng.randint(0, self.cols - 1), rng.randint(0, self.rows - 1)
            if self.map[y][x] in [WALL, WATER, COVER, BUSH, BOX]:
                self.map[y][x] = WALKABLE

    def crossover(self, other, rng):
        child = BrawlStarsMap(size=(self.rows, self.cols))
        split_point = rng.randint(0, self.cols - 1)
        for y in range(self.rows):
            for x in range(self.cols):
                child.map[y][x] = self.map[y][x] if x <= split_point else other.map[y][x]
        child._repair_spawns(rng)
        return child

    def _repair_spawns(self, rng):
        spawns = get_positions(self.map, SPAWN)  # list of (y, x)
        while len(spawns) > 10:
            y, x = spawns.pop()
            self.map[y][x] = WALKABLE
        while True:
            spawns = get_positions(self.map, SPAWN)
            if len(spawns) >= 10:
                break
            y = rng.randint(0, self.rows - 1)
            x = rng.randint(0, self.cols - 1)
            if self.map[y][x] == WALKABLE:
                self.map[y][x] = SPAWN


# ------------------------
# Genetic Algorithm Runner
# ------------------------
def run_ga(population_size=50, generations=100, seed=None):
    rng = random.Random(seed)

    population = [BrawlStarsMap.random_map(rng=rng) for _ in range(population_size)]

    for gen in range(generations):
        # Evaluate fitness
        for ind in population:
            ind.fitness = evaluate_map_fitness(ind.map)

        # Sort by fitness
        population.sort(key=lambda x: x.fitness, reverse=True)
        print(f"Generation {gen}: Best fitness = {population[0].fitness}")

        # Selection and reproduction
        new_population = []
        elite_count = max(1, population_size // 10)
        new_population.extend(copy.deepcopy(population[:elite_count]))

        while len(new_population) < population_size:
            p1 = tournament_select(population, rng)
            p2 = tournament_select(population, rng)
            child = p1.crossover(p2, rng)
            if rng.random() < 0.90:  # mutation rate
                child.mutate(rng)
            new_population.append(child)

        population = new_population

    return population[0]

def tournament_select(population, rng, tournament_size=3):
    contestants = rng.sample(population, tournament_size)
    return max(contestants, key=lambda x: x.fitness)


# ---- Export for Unity (IDs) ----
ID_MAP = {
    WALKABLE: 0,
    WALL:     1,
    BUSH:     2,
    SPAWN:    3,
    COVER:    4,
    WATER:    5,
    BOX:      6,
}

def save_map_txt_strgrid(str_grid, path):
    with open(path, "w", newline="\n") as f:
        for row in str_grid:
            f.write(" ".join(str(ID_MAP.get(cell, 0)) for cell in row) + "\n")


if __name__ == "__main__":
    best_map = run_ga(population_size=60, generations=80)  # seed=None => different each run
    print(f"Final fitness: {best_map.fitness}")
    # from datetime import datetime
    # out = f"best_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    out = f"best_map.txt"
    save_map_txt_strgrid(best_map.map, out)
    print("Saved TXT to", out)
