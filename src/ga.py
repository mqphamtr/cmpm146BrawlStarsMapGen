import random
import copy
from collections import deque
from fitness import evaluate_map_fitness, WALKABLE, WALL, WATER, COVER, BOX, SPAWN, BUSH

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
        max_attempts = 500  # safety cutoff

        while len(spawns) < 10 and attempts < max_attempts:
            x = random.randint(center_x-25, center_x+25)
            y = random.randint(center_y-25, center_y+25)
            if self._valid_spawn_position((x,y), spawns):
                spawns.append((x,y))
            attempts += 1

        if len(spawns) < 10:
            print(f"⚠️ Only placed {len(spawns)} spawn points (not 10) after {max_attempts} attempts")

        return spawns


    def _valid_spawn_position(self, new_pos, existing):
        """Check if a spawn position is valid"""
        x, y = new_pos
        if x < 0 or x >= self.cols or y < 0 or y >= self.rows:
            return False
        # Check minimum distance from other spawns
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
        
        # Place remaining boxes
        while placed < count:
            x = random.randint(0, self.cols-1)
            y = random.randint(0, self.rows-1)
            if self.map[y][x] == WALKABLE:
                self.map[y][x] = BOX
                placed += 1

    def _add_obstacles(self):
        """Add obstacles (walls, water, cover) targeting 15% density"""
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
        """Add bushes targeting 10% density"""
        target_count = int(self.rows * self.cols * 0.10)
        placed = 0
        
        while placed < target_count:
            x = random.randint(0, self.cols-1)
            y = random.randint(0, self.rows-1)
            if self.map[y][x] == WALKABLE:
                self.map[y][x] = BUSH
                placed += 1

    def mutate(self):
        """Mutate the map while maintaining validity"""
        mutation_types = ['swap', 'add_obstacle', 'remove_obstacle', 'add_bush', 'remove_bush']
        mutation = random.choice(mutation_types)
        
        if mutation == 'swap':
            # Swap two non-spawn tiles
            for _ in range(10):  # Try 10 times
                x1, y1 = random.randint(0, self.cols-1), random.randint(0, self.rows-1)
                x2, y2 = random.randint(0, self.cols-1), random.randint(0, self.rows-1)
                if self.map[y1][x1] != SPAWN and self.map[y2][x2] != SPAWN:
                    self.map[y1][x1], self.map[y2][x2] = self.map[y2][x2], self.map[y1][x1]
                    break
        elif mutation == 'add_obstacle':
            self._add_obstacles()
        elif mutation == 'remove_obstacle':
            # Remove a random obstacle
            obstacles = [(x,y) for y in range(self.rows) for x in range(self.cols) 
                       if self.map[y][x] in [WALL, WATER, COVER]]
            if obstacles:
                x, y = random.choice(obstacles)
                self.map[y][x] = WALKABLE
        elif mutation == 'add_bush':
            self._add_bushes()
        elif mutation == 'remove_bush':
            # Remove a random bush
            bushes = [(x,y) for y in range(self.rows) for x in range(self.cols) 
                     if self.map[y][x] == BUSH]
            if bushes:
                x, y = random.choice(bushes)
                self.map[y][x] = WALKABLE

    def crossover(self, other):
        """Perform crossover with another map"""
        child = BrawlStarsMap()
        
        # Vertical split
        split_point = random.randint(0, self.cols)
        for y in range(self.rows):
            for x in range(self.cols):
                if x < split_point:
                    child.map[y][x] = self.map[y][x]
                else:
                    child.map[y][x] = other.map[y][x]
        
        # Ensure valid spawn points
        spawn_points = self._generate_spawn_points()
        for x, y in spawn_points:
            child.map[y][x] = SPAWN
            
        return child

def run_ga(population_size=50, generations=10): #set to 10 generations for testing was 100
    """Run the genetic algorithm"""
    # Initialize population
    print 
    population = [BrawlStarsMap.random_map() for _ in range(population_size)]
    
    for gen in range(generations):
        # Evaluate fitness
        for individual in population:
            individual.fitness = evaluate_map_fitness(individual.map)
        
        # Sort by fitness
        population.sort(key=lambda x: x.fitness, reverse=True)
        
        # Print progress
        print(f"Generation {gen}: Best fitness = {population[0].fitness}")
        
        # Selection and reproduction
        new_population = []
        
        # keep best 10%
        elite_count = max(1, population_size // 10)
        new_population.extend(copy.deepcopy(population[:elite_count]))
        
        # Generate rest of population
        while len(new_population) < population_size:
            # Tournament selection
            parent1 = tournament_select(population)
            parent2 = tournament_select(population)
            
            # Crossover
            child = parent1.crossover(parent2)
            
            # Mutation
            if random.random() < 0.1:  # 10% mutation rate
                child.mutate()
            
            new_population.append(child)
        
        population = new_population
    
    return population[0]  # Return best individual

def tournament_select(population, tournament_size=3):
    """Tournament selection"""
    tournament = random.sample(population, tournament_size)
    return max(tournament, key=lambda x: x.fitness)

if __name__ == "__main__":
    best_map = run_ga()
    print(f"Final fitness: {best_map.fitness}")