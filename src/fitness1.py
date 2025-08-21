from collections import deque
import math

# Tile constants 
WALKABLE = "empty"
WALL = "wall"
WATER = "water"
COVER = "cover"
# BREAKABLE = "breakable"
BOX = "box"
SPAWN = "spawn"
BUSH = "bush"
# FENCE = "fence"

# Main Fitness Function
def evaluate_map_fitness(game_map):
    """
    Evaluate the fitness of a Brawl Stars map.
    """

    score = 0

    # Hard Constraints
    if not valid_size(game_map):
        print("❌ Invalid size")
        return 0
    if not valid_player_count(game_map):
        print("❌ Wrong number of players")
        return 0
    if not valid_box_count(game_map):
        print("❌ Wrong number of boxes")
        return 0
    if not all_clusters_valid(game_map):
        print("❌ Invalid clusters")
        return 0
    if not player_box_distance_ok(game_map):
        print("❌ Player-box distance rule failed")
        return 0
    if not central_area_ok(game_map):
        print("❌ Central area missing boxes")
        return 0
    if not all_tiles_reachable(game_map):
        print("❌ Not all tiles reachable")
        return 0
    if not close_spawns_have_barriers(game_map):
        print("❌ Spawn barrier rule failed")
        return 0

    # Soft Constraints
    score += symmetry_score(game_map) * 2
    score += obstacle_distribution_score(game_map) * 1.5
    score += bush_distribution_score(game_map) * 1.5
    score += box_distribution_score(game_map) * 2
    score += pathing_quality_score(game_map) * 1
    score += spawn_layout_score(game_map) * 2

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

def all_clusters_valid(game_map):
    # Placeholder: Implement cluster rules for walls, fences, bushes, and boxes
    return True

def player_box_distance_ok(game_map):
    player_positions = get_positions(game_map, SPAWN)
    box_positions = get_positions(game_map, BOX)
    for player in player_positions:
        if min_tile_distance(game_map, player, box_positions) > 20:
            return False
    return True

def central_area_ok(game_map):
    center = get_map_center(game_map)
    center_boxes = count_boxes_in_radius(game_map, center, radius=8)
    return center_boxes >= 8

def all_tiles_reachable(game_map):
    walkable_tiles = {WALKABLE, BOX, BUSH, SPAWN}
    start = get_first_walkable_tile(game_map)
    if not start:
        return False
    reachable = bfs_count(game_map, start, walkable_tiles)
    total_walkable = sum(tile in walkable_tiles for row in game_map for tile in row)
    return reachable == total_walkable

def close_spawns_have_barriers(game_map):
    spawns = get_positions(game_map, SPAWN)
    for i, a in enumerate(spawns):
        for j, b in enumerate(spawns):
            if i < j:
                if min_tile_distance(game_map, a, [b]) < 18:
                    if not has_barrier_between(game_map, a, b, min_len=10, max_len=14):
                        return False
    return True


# Soft Scoring Functions
def symmetry_score(game_map):
    rows, cols = len(game_map), len(game_map[0])
    mismatch = 0
    total = 0
    for r in range(rows):
        for c in range(cols):
            if game_map[r][c] != game_map[r][cols - 1 - c]:
                mismatch += 1
            total += 1
    return max(0, 1 - mismatch / total) * 10

def obstacle_distribution_score(game_map):
    obstacles = {WALL, WATER, COVER}
    obstacle_count = sum(tile in obstacles for row in game_map for tile in row)
    total_tiles = len(game_map) * len(game_map[0])
    density = obstacle_count / total_tiles
    return max(0, 1 - abs(density - 0.15) * 10) * 5  # target 15% obstacles

def bush_distribution_score(game_map):
    bushes = count_tiles(game_map, BUSH)
    total_tiles = len(game_map) * len(game_map[0])
    density = bushes / total_tiles
    return max(0, 1 - abs(density - 0.10) * 10) * 5  # target 10% bushes

def box_distribution_score(game_map):
    box_positions = get_positions(game_map, BOX)
    if not box_positions:
        return 0
    avg_dist = sum(
        min_tile_distance(game_map, box, [p]) for box in box_positions for p in get_positions(game_map, SPAWN)
    ) / len(box_positions)
    return max(0, min(avg_dist / 10, 1)) * 5

def pathing_quality_score(game_map):
    # Placeholder: Could check for choke points and alternative paths
    return 5

def spawn_layout_score(game_map):
    # Placeholder: reward if 4 in corners and 6 near center
    return 5


# Utility Functions
def count_tiles(game_map, tile_type):
    return sum(row.count(tile_type) for row in game_map)

def get_positions(game_map, tile_type):
    return [(r, c) for r, row in enumerate(game_map) for c, val in enumerate(row) if val == tile_type]

def get_map_center(game_map):
    return (len(game_map) // 2, len(game_map[0]) // 2)

def count_boxes_in_radius(game_map, center, radius):
    cr, cc = center
    return sum(
        1
        for r, row in enumerate(game_map)
        for c, val in enumerate(row)
        if val == BOX and math.dist((r, c), center) <= radius
    )

def get_first_walkable_tile(game_map):
    walkable = {WALKABLE, BOX, BUSH, SPAWN}
    for r, row in enumerate(game_map):
        for c, val in enumerate(row):
            if val in walkable:
                return (r, c)
    return None

def bfs_count(game_map, start, walkable_tiles):
    visited = set([start])
    queue = deque([start])
    while queue:
        r, c = queue.popleft()
        for dr, dc in [(1,0),(-1,0),(0,1),(0,-1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < len(game_map) and 0 <= nc < len(game_map[0]):
                if (nr, nc) not in visited and game_map[nr][nc] in walkable_tiles:
                    visited.add((nr, nc))
                    queue.append((nr, nc))
    return len(visited)

def min_tile_distance(game_map, start, targets):
    # BFS orthogonal only
    visited = set([start])
    queue = deque([(start[0], start[1], 0)])
    while queue:
        r, c, d = queue.popleft()
        if (r, c) in targets:
            return d
        for dr, dc in [(1,0),(-1,0),(0,1),(0,-1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < len(game_map) and 0 <= nc < len(game_map[0]):
                if (nr, nc) not in visited and game_map[nr][nc] != WALL and game_map[nr][nc] != WATER and game_map[nr][nc] != COVER:
                    visited.add((nr, nc))
                    queue.append((nr, nc, d + 1))
    return float("inf")

def has_barrier_between(game_map, a, b, min_len, max_len):
    # Placeholder: Simplified check that there are enough obstacle tiles in straight/near line
    return True  

