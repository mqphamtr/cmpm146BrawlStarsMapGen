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
                score += 1
    return score

# Utility Functions
def count_tiles(game_map, tile_type):
    return sum(row.count(tile_type) for row in game_map)

def get_positions(game_map, tile_type):
    return [(r, c) for r, row in enumerate(game_map) for c, val in enumerate(row) if val == tile_type]
