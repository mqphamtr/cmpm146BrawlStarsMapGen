from collections import deque
import math

# Tile Constants
WALKABLE = "empty"
WALL = "wall"
WATER = "water"
COVER = "cover"
BOX = "box"
SPAWN = "spawn"
BUSH = "bush"

TRAVERSABLE = {WALKABLE, BOX, SPAWN, BUSH}

# Main Fitness Function
def evaluate_map_fitness(game_map):
    """
    Evaluate the fitness of a Brawl Stars map.
    Returns 0 if any hard constraint fails.
    """
    # Hard Constraints
    if not valid_size(game_map):
        return 0
    if not valid_player_count(game_map):
        return 0
    if not valid_box_count(game_map):
        return 0

    #soft scoring
    score = 0
    score += symmetry_score(game_map)
    score += reachable_tiles_score(game_map)
    score += central_area_score(game_map)
    score += wall_cluster_score(game_map)

    return score

# Hard Constraint Checks
def valid_size(game_map):
    rows, cols = len(game_map), len(game_map[0])
    return (rows, cols) in [(60, 60), (64, 64)]

def valid_player_count(game_map):
    return count_tiles(game_map, SPAWN) == 10

def valid_box_count(game_map):
    box_count = count_tiles(game_map, BOX)
    return 20 <= box_count <= 35

# Soft Constraint Functions

def symmetry_score(game_map):
    """
    Returns a score based on how many tiles are mirrored left-to-right.
    One point for each matching pair.
    """
    rows, cols = len(game_map), len(game_map[0])
    score = 0
    for r in range(rows):
        for c in range(cols // 2):
            left_tile = game_map[r][c]
            right_tile = game_map[r][cols - c - 1]
            if left_tile == right_tile:
                score += 5 #score
    return score

def reachable_tiles_score(game_map):
    rows, cols = len(game_map), len(game_map[0])

    traversable_positions = [
        (r, c) for r in range(rows) for c in range(cols)
        if game_map[r][c] in TRAVERSABLE
    ]

    if not traversable_positions:
        return 0

    start = traversable_positions[0]
    visited = set([start])
    queue = deque([start])

    while queue:
        r, c = queue.popleft()
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                if (nr, nc) not in visited and game_map[nr][nc] in TRAVERSABLE:
                    visited.add((nr, nc))
                    queue.append((nr, nc))

    return len(visited)

def central_area_score(game_map):
    """
    Returns a score based on the number of desirable tiles in the central area.
    Central area is a square 8x8 to 12x12 in the center.
    Tiles considered good: WALKABLE, BUSH, BOX.
    """
    rows, cols = len(game_map), len(game_map[0])
    center_r, center_c = rows // 2, cols // 2

    # Randomize size between 8 and 12
    import random
    size = random.randint(8, 12)
    half = size // 2

    # Define bounds of central area
    r_start = max(0, center_r - half)
    r_end = min(rows, center_r + half)
    c_start = max(0, center_c - half)
    c_end = min(cols, center_c + half)

    # Count desirable tiles
    desirable = {BUSH, BOX, WALKABLE}
    score = 0
    for r in range(r_start, r_end):
        for c in range(c_start, c_end):
            if game_map[r][c] in desirable:
                score += 5 #score

    return score

def wall_cluster_score(game_map):
    """
    Reward WALL tiles for forming contiguous clusters.
    Each cluster contributes cluster_size^1.5 points.
    Tiles are only counted once per cluster.
    """
    rows, cols = len(game_map), len(game_map[0])
    visited = set()
    total_score = 0

    for r in range(rows):
        for c in range(cols):
            if game_map[r][c] == WALL and (r, c) not in visited:
                # Explore this cluster
                cluster_size = 0
                stack = [(r, c)]
                visited.add((r, c))

                while stack:
                    cr, cc = stack.pop()
                    cluster_size += 1
                    # Check orthogonal neighbors
                    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                        nr, nc = cr+dr, cc+dc
                        if 0 <= nr < rows and 0 <= nc < cols:
                            if game_map[nr][nc] == WALL and (nr, nc) not in visited:
                                visited.add((nr, nc))
                                stack.append((nr, nc))

                # Reward cluster based on size
                total_score += cluster_size ** 2.7

    return total_score

# Utility Functions
def count_tiles(game_map, tile_type):
    return sum(row.count(tile_type) for row in game_map)

def get_positions(game_map, tile_type):
    return [(r, c) for r, row in enumerate(game_map) for c, val in enumerate(row) if val == tile_type]
