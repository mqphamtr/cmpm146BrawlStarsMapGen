from enum import IntEnum

class Tile(IntEnum):
    EMPTY = 0
    WALL = 1
    BUSH = 2
    SPAWN_A = 3
    SPAWN_B = 4
    POWER_ITEM = 5

LEGEND = {t.name: int(t) for t in Tile}

#maps height and width
MAP_H, MAP_W = 60, 60

MUTABLE_TILES = (Tile.EMPTY, Tile.WALL, Tile.BUSH, Tile.POWER_ITEM)
