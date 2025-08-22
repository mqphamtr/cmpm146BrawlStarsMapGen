import random
import copy
from fitness import evaluate_map_fitness, WALKABLE, WALL, WATER, COVER, BOX, SPAWN, BUSH, get_positions

class BrawlStarsMap:
    def __init__(self, size=(60, 60)):
        self.rows, self.cols = size
        self.map = [[WALKABLE for _ in range(self.cols)] for _ in range(self.rows)]
        self.fitness = None

    @classmethod
    def random_map(cls):
        """Generate a random valid map"""
        map_instance = cls()
        
        # Place 10 spawn points
        spawn_points = map_instance._generate_spawn_points()
        for x, y in spawn_points:
            map_instance.map[y][x] = SPAWN
        
        # Place boxes (20-35)
        box_count = random.randint(20, 35)
        map_instance._place_boxes(box_count)
        
        # Add obstacles and bushes
        map_instance._add_obstacles()
        map_instance._add_bushes()
        
        return map_instance

    def _generate_spawn_points(self):
        """Generate up to 10 spawn points with valid distances"""
        spawns = []
        # 4 corners
        corner_positions = [(5,5), (self.cols-6,5), (5,self.rows-6), (self.cols-6,self.rows-6)]
        spawns.extend(corner_positions)
    
        # 6 more positions near center
        center_x, center_y = self.cols//2, self.rows//2
        attempts = 0
        max_attempts = 500

        while len(spawns) < 10 and attempts < max_attempts:
            x = random.randint(center_x-25, center_x+25)
            y = random.randint(center_y-25, center_y+25)
            if self._valid_spawn_position((x,y), spawns):
                spawns.append((x,y))
            attempts += 1

        if len(spawns) < 10:
            print(f"⚠️ Only placed {len(spawns)} spawn points after {max_attempts} attempts")

        return spawns

    def _valid_spawn_position(self, new_pos, existing):
        """Check if a spawn position is valid"""
        x, y = new_pos
        if x < 0 or x >= self.cols or y < 0 or y >= self.rows:
            return False
        for ex, ey in existing:
            if abs(ex-x) + abs(ey-y) < 18:  # Manhattan distance
                return False
        return True

    def _place_boxes(self, count):
        """Place boxes ensuring valid distribution"""
        center_x, center_y = self.cols//2, self.rows//2
        placed = 0
        
        # Ensure center area has enough boxes
        center_boxes = max(8, count // 4)
        for _ in range(center_boxes):
            x = random.randint(center_x-8, center_x+8)
            y = random.randint(center_y-8, center_y+8)
            if self.map[y][x] == WALKABLE:
                self.map[y][x] = BOX
                placed += 1
        
        while placed < count:
            x = random.randint(0, self.cols-1)
            y = random.randint(0, self.rows-1)
            if self.map[y][x] == WALKABLE:
                self.map[y][x] = BOX
                placed += 1

    def _add_obstacles(self):
        target_count = int(self.rows * self.cols * 0.15)
        obstacles = [WALL, WATER, COVER]
        placed = 0
        
        while placed < target_count:
            x = random.randint(0, self.cols-1)
            y = random.randint(0, self.rows-1)
            if self.map[y][x] == WALKABLE:
                self.map[y][x] = random.choice(obstacles)
                placed += 1

    def _add_bushes(self):
        target_count = int(self.rows * self.cols * 0.10)
        placed = 0
        
        while placed < target_count:
            x = random.randint(0, self.cols-1)
            y = random.randint(0, self.rows-1)
            if self.map[y][x] == WALKABLE:
                self.map[y][x] = BUSH
                placed += 1

    # ------------------------
    # Genetic Algorithm Helpers
    # ------------------------
    def mutate(self):
        """Small mutations for gradual evolution"""
        mutation_types = ['swap', 'add_tile', 'remove_tile']
        mutation = random.choice(mutation_types)

        if mutation == 'swap':
            for _ in range(10):
                x1, y1 = random.randint(0, self.cols-1), random.randint(0, self.rows-1)
                x2, y2 = random.randint(0, self.cols-1), random.randint(0, self.rows-1)
                if self.map[y1][x1] != SPAWN and self.map[y2][x2] != SPAWN:
                    self.map[y1][x1], self.map[y2][x2] = self.map[y2][x2], self.map[y1][x1]
                    break
        elif mutation == 'add_tile':
            x, y = random.randint(0, self.cols-1), random.randint(0, self.rows-1)
            if self.map[y][x] == WALKABLE:
                self.map[y][x] = random.choice([WALL, WATER, COVER, BUSH, BOX])
        elif mutation == 'remove_tile':
            x, y = random.randint(0, self.cols-1), random.randint(0, self.rows-1)
            if self.map[y][x] in [WALL, WATER, COVER, BUSH, BOX]:
                self.map[y][x] = WALKABLE

    def crossover(self, other):
        """Combine two maps preserving structure"""
        child = BrawlStarsMap()
        split_point = random.randint(0, self.cols-1)
        for y in range(self.rows):
            for x in range(self.cols):
                child.map[y][x] = self.map[y][x] if x <= split_point else other.map[y][x]
        child._repair_spawns()
        return child

    def _repair_spawns(self):
        """Ensure exactly 10 spawn points"""
        current_spawns = get_positions(self.map, SPAWN)
        while len(current_spawns) < 10:
            x, y = random.randint(0, self.cols-1), random.randint(0, self.rows-1)
            if self.map[y][x] == WALKABLE:
                self.map[y][x] = SPAWN
                current_spawns.append((y, x))
        while len(current_spawns) > 10:
            y, x = current_spawns.pop()
            self.map[y][x] = WALKABLE


# ------------------------
# Genetic Algorithm Runner
# ------------------------
def run_ga(population_size=50, generations=100):
    population = [BrawlStarsMap.random_map() for _ in range(population_size)]
    
    for gen in range(generations):
        # Evaluate fitness
        for individual in population:
            individual.fitness = evaluate_map_fitness(individual.map)
        
        # Sort by fitness
        population.sort(key=lambda x: x.fitness, reverse=True)
        print(f"Generation {gen}: Best fitness = {population[0].fitness}")
        
        # Selection and reproduction
        new_population = []

        # Keep top 10% elite
        elite_count = max(1, population_size // 10)
        new_population.extend(copy.deepcopy(population[:elite_count]))

        while len(new_population) < population_size:
            parent1 = tournament_select(population)
            parent2 = tournament_select(population)
            child = parent1.crossover(parent2)
            if random.random() < 0.1:  # mutation rate
                child.mutate()
            new_population.append(child)

        population = new_population

    return population[0]

def tournament_select(population, tournament_size=3):
    tournament = random.sample(population, tournament_size)
    return max(tournament, key=lambda x: x.fitness)


if __name__ == "__main__":
    best_map = run_ga()
    print(f"Final fitness: {best_map.fitness}")
