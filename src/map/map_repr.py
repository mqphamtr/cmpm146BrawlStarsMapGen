from dataclasses import dataclass
import numpy as np
from .tiles import Tile, MAP_H, MAP_W, MUTABLE_TILES

@dataclass
class BSMap:
    grid: np.ndarray

    @staticmethod
    def empty(h=MAP_H, w=MAP_W) -> "BSMap":
        return BSMap(np.zeros((h, w), dtype=np.uint8))

    @staticmethod
    def random(h=MAP_H, w=MAP_W, p_wall=0.12, p_bush=0.18) -> "BSMap":
        g = np.zeros((h, w), dtype=np.uint8)
        mask = np.random.rand(h, w)
        g[mask < p_wall] = Tile.WALL
        g[(mask >= p_wall) & (mask < p_wall + p_bush)] = Tile.BUSH

        g[h // 2, 2] = Tile.SPAWN_A
        g[h // 2, w - 3] = Tile.SPAWN_B
        return BSMap(g)

    def copy(self) -> "BSMap":
        return BSMap(self.grid.copy())

    def to_ascii(self) -> str:
        CH = {Tile.EMPTY: " .", Tile.WALL: " #", Tile.BUSH: " ~",
              Tile.SPAWN_A: " A", Tile.SPAWN_B: " B", Tile.POWER_ITEM: " *"}
        return "\n".join("".join(CH.get(int(x), " ?") for x in row) for row in self.grid)
