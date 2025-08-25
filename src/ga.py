import copy
import random
from fitness import (
    evaluate_map_fitness, WALKABLE, WALL, WATER, COVER, BOX, SPAWN, BUSH, get_positions
)

import collections
import map_sliders

PASSABLE = {WALKABLE, BUSH, SPAWN}
OBSTACLE = {WALL, WATER, COVER, BOX}

DEFAULT_CLEARANCE = map_sliders.DEFAULT_CLEARANCE
CORRIDOR_WIDTH = map_sliders.CORRIDOR_WIDTH
MAP_SIZE = map_sliders.MAP_SIZE
MIN_SPAWN_DIST = MAP_SIZE/5



class BrawlStarsMap:
    def __init__(self, size=(MAP_SIZE, MAP_SIZE), symmetry_axis="vertical", clearance=DEFAULT_CLEARANCE):
        self.rows, self.cols = size
        self.map = [[WALKABLE for _ in range(self.cols)] for _ in range(self.rows)]
        self.fitness = None
        self.symmetry_axis = symmetry_axis 
        self.clearance = clearance                          # how much empty space around an element

    @classmethod
    def random_map(cls, rng, max_tries=20):
        for _ in range(max_tries):
            m = cls()
            for x, y in m._generate_spawn_points(rng):          #create spawn points
                m.map[y][x] = SPAWN

            m._place_structures_half(rng)                          # build half a map
            m._apply_symmetry()                                    # apply symmetry

            m._ensure_spawn_connectivity()                          # Connectivity repair (carves minimal corridors if needed)

            if evaluate_map_fitness(m.map) > 0:
                return m
        return m

    def _generate_spawn_points(self, rng):                                              # Spawn placement (y, x)
        spawns = [(5,5), (self.cols-6,5), (5,self.rows-6), (self.cols-6,self.rows-6)]   # Four corners-ish + 6 random (mirrored-friendly by pairing)
        cx, cy = self.cols // 2, self.rows // 2
        attempts = 0
        while len(spawns) < 10 and attempts < 500:
            if self.symmetry_axis == "vertical":                                        # sample on left/top half then mirror its pair to enforce symmetry
                x = rng.randint(2, cx-2)
                y = rng.randint(2, self.rows-3)
                pair = (self.cols-1-x, y)
            else:
                x = rng.randint(2, self.cols-3)
                y = rng.randint(2, cy-2)
                pair = (x, self.rows-1-y)
            cand = (x, y)
            if self._valid_spawn_position(cand, spawns) and self._valid_spawn_position(pair, spawns):
                spawns.append((x, y))
                if len(spawns) < 10:
                    spawns.append(pair)
            attempts += 1
        return spawns[:10]

    def _valid_spawn_position(self, new_pos, existing):
        x, y = new_pos
        if x < 0 or x >= self.cols or y < 0 or y >= self.rows:
            return False
        for ex, ey in existing:
            if abs(ex - x) + abs(ey - y) < MIN_SPAWN_DIST:
                return False
        return True

    def _place_structures_half(self, rng):
        # HALF-side targets; mirrored => doubled overall
        targets = {
            "water_lines": rng.randint(map_sliders.MIN_WATER_LINE, map_sliders.MAX_WATER_LINE),
            "wall_blocks": rng.randint(map_sliders.MIN_WALL_BLOCKS, map_sliders.MAX_WALL_BLOCKS),
            "cover_clusters": rng.randint(map_sliders.MIN_COVER_CLUSTERS, map_sliders.MAX_COVER_CLUSTERS),
            "bush_patches": rng.randint(map_sliders.MIN_BUSH_PATCHES, map_sliders.MAX_BUSH_PATCHES),
            "boxes": rng.randint(map_sliders.MIN_BOXES, map_sliders.MAX_BOXES),
        }

        # WATER: thicker/longer, plus some reservoirs
        for _ in range(targets["water_lines"]):
            if rng.random() < 0.55:
                self._try_stamp_line_half(rng, WATER, min_len=14, max_len=28, thickness=rng.randint(2,3))
            else:
                self._try_stamp_rect_half(rng, WATER, w=rng.randint(5,9), h=rng.randint(10,16))

        # WALL blocks: medium rectangles
        for _ in range(targets["wall_blocks"]):
            self._try_stamp_rect_half(rng, WALL, w=rng.randint(4,10), h=rng.randint(4,10))

        # COVER clusters: tighter blobs
        for _ in range(targets["cover_clusters"]):
            self._try_stamp_blob_half(rng, COVER, radius=rng.randint(3,5), p=0.7)

        # BOX clumps: more frequent
        for _ in range(targets["boxes"]):
            self._try_stamp_rect_half(rng, BOX, w=rng.randint(2,10), h=rng.randint(2,10))

        # BUSH patches: bigger organic areas
        for _ in range(targets["bush_patches"]):
            self._try_stamp_blob_half(rng, BUSH, radius=rng.randint(4,7), p=0.7)


    # ---- helper functions for generating half maps
    def _half_bounds(self):
        if self.symmetry_axis == "vertical":
            return (0, self.rows-1, 0, (self.cols//2)-1)  # y0,y1,x0,x1 (inclusive)
        else:
            return (0, (self.rows//2)-1, 0, self.cols-1)

    def _try_stamp_line_half(self, rng, tile, min_len, max_len, thickness=1):
        y0, y1, x0, x1 = self._half_bounds()
        if self.symmetry_axis == "vertical":
            x = rng.randint(x0+2, x1-2)
            y_start = rng.randint(y0+2, y1-2)
            length = rng.randint(min_len, max_len)
            vertical = rng.random() < 0.5
            if vertical:
                y_end = max(y0+2, min(y1-2, y_start + (rng.choice([-1,1]) * length)))
                xL, xR = x, x + thickness - 1
                if self._area_clear_with_clearance(xL, min(y_start,y_end), xR, max(y_start,y_end)):
                    self._paint_line((x, y_start), (x, y_end), tile, thickness)
            else:
                x_end = max(x0+2, min(x1-2, x + (rng.choice([-1,1]) * length)))
                yT, yB = y_start, y_start + thickness - 1
                if self._area_clear_with_clearance(min(x, x_end), yT, max(x, x_end), yB):
                    self._paint_line((x, y_start), (x_end, y_start), tile, thickness)
        else:
            y = rng.randint(y0+2, y1-2)
            x_start = rng.randint(x0+2, x1-2)
            length = rng.randint(min_len, max_len)
            horizontal = rng.random() < 0.5
            if horizontal:
                x_end = max(x0+2, min(x1-2, x_start + (rng.choice([-1,1]) * length)))
                yT, yB = y, y + thickness - 1
                if self._area_clear_with_clearance(min(x_start,x_end), yT, max(x_start,x_end), yB):
                    self._paint_line((x_start, y), (x_end, y), tile, thickness)
            else:
                y_end = max(y0+2, min(y1-2, y + (rng.choice([-1,1]) * length)))
                xL, xR = x_start, x_start + thickness - 1
                if self._area_clear_with_clearance(xL, min(y,y_end), xR, max(y,y_end)):
                    self._paint_line((x_start, y), (x_start, y_end), tile, thickness)

    def _try_stamp_rect_half(self, rng, tile, w, h):
        y0, y1, x0, x1 = self._half_bounds()
        x = rng.randint(x0+2, max(x0+2, x1 - w - 1))
        y = rng.randint(y0+2, max(y0+2, y1 - h - 1))
        if self._area_clear_with_clearance(x, y, x+w-1, y+h-1):
            self._paint_rect(x, y, w, h, tile)

    def _try_stamp_blob_half(self, rng, tile, radius=4, p=0.6):
        y0, y1, x0, x1 = self._half_bounds()
        cx = rng.randint(x0+2+radius, x1-2-radius)
        cy = rng.randint(y0+2+radius, y1-2-radius)
        xL, xR, yT, yB = cx - radius, cx + radius, cy - radius, cy + radius
        if self._area_clear_with_clearance(xL, yT, xR, yB):
            self._paint_blob(cx, cy, radius, tile, p)
    
    def _paint_line(self, a, b, tile, thickness=1):
        x0, y0 = a; x1, y1 = b
        if x0 == x1:
            y_start, y_end = sorted([y0, y1])
            for y in range(y_start, y_end+1):
                for dx in range(thickness):
                    self._set_if_empty(x0+dx, y, tile)
            self._clearance_halo(x0, y_start, x0+thickness-1, y_end)
        elif y0 == y1:
            x_start, x_end = sorted([x0, x1])
            for x in range(x_start, x_end+1):
                for dy in range(thickness):
                    self._set_if_empty(x, y0+dy, tile)
            self._clearance_halo(x_start, y0, x_end, y0+thickness-1)
        else:
            # simple Bresenham for diagonals (optional)
            dx = 1 if x1 >= x0 else -1
            dy = 1 if y1 >= y0 else -1
            x, y = x0, y0
            while True:
                self._set_if_empty(x, y, tile)
                if x == x1 and y == y1: break
                if abs(x - x1) > abs(y - y1): x += dx
                else: y += dy
            self._clearance_halo(min(x0,x1), min(y0,y1), max(x0,x1), max(y0,y1))

    def _paint_rect(self, x, y, w, h, tile):
        for yy in range(y, y+h):
            for xx in range(x, x+w):
                self._set_if_empty(xx, yy, tile)
        self._clearance_halo(x, y, x+w-1, y+h-1)

    def _paint_blob(self, cx, cy, r, tile, p=0.6):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if 0 <= xx < self.cols and 0 <= yy < self.rows:
                    if (xx-cx)**2 + (yy-cy)**2 <= r*r and random.random() < p:
                        self._set_if_empty(xx, yy, tile)
        self._clearance_halo(cx - r, cy - r, cx + r, cy + r)

    def _set_if_empty(self, x, y, tile):
        if 0 <= x < self.cols and 0 <= y < self.rows:
            if self.map[y][x] == WALKABLE or tile == BUSH:  # allow overlaying bushes onto walkable only
                self.map[y][x] = tile

    # Clearance handling
    def _area_clear_with_clearance(self, xL, yT, xR, yB):
        # require the expanded bbox to be strictly WALKABLE (so we keep corridors)
        c = self.clearance
        for yy in range(max(0, yT - c), min(self.rows, yB + c + 1)):
            for xx in range(max(0, xL - c), min(self.cols, xR + c + 1)):
                if self.map[yy][xx] != WALKABLE and self.map[yy][xx] != SPAWN:
                    return False
        return True

    def _clearance_halo(self, xL, yT, xR, yB):
        c = self.clearance
        for yy in range(max(0, yT - c), min(self.rows, yB + c + 1)):
            for xx in range(max(0, xL - c), min(self.cols, xR + c + 1)):
                # do not overwrite the element itself
                if not (xL <= xx <= xR and yT <= yy <= yB):
                    if self.map[yy][xx] not in {SPAWN}:
                        self.map[yy][xx] = WALKABLE

    def _apply_symmetry(self):
        if self.symmetry_axis == "vertical":
            for y in range(self.rows):
                for x in range(self.cols // 2):
                    mirror_x = self.cols - 1 - x
                    self.map[y][mirror_x] = self.map[y][x]
        else:
            for y in range(self.rows // 2):
                mirror_y = self.rows - 1 - y
                self.map[mirror_y] = list(self.map[y])

    def _reimpose_symmetry(self):
        self._apply_symmetry()

    def _ensure_spawn_connectivity(self):
        spawns = [(x, y) for (y, x) in get_positions(self.map, SPAWN)]
        if not spawns:
            return
        root = spawns[0]
        reachable = self._bfs_passable_from(root)
        if all(s in reachable for s in spawns):
            return
        # carve minimal corridors from root to each unreachable spawn
        for s in spawns:
            if s not in reachable:
                path = self._bfs_any_cost(root, s)  # path through anything
                if path:
                    for (x, y) in path:
                        if self.map[y][x] in OBSTACLE:
                            self.map[y][x] = WALKABLE
                    # keep a little space around the corridor
                    self._clearance_halo_along_path(path)
                # recompute reachability after each carve
                reachable = self._bfs_passable_from(root)

    def _bfs_passable_from(self, start):
        sx, sy = start
        q = collections.deque([(sx, sy)])
        seen = {start}
        while q:
            x, y = q.popleft()
            for nx, ny in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
                if 0 <= nx < self.cols and 0 <= ny < self.rows:
                    if (nx, ny) not in seen and self.map[ny][nx] in PASSABLE:
                        seen.add((nx, ny))
                        q.append((nx, ny))
        return seen

    def _bfs_any_cost(self, start, goal):
        sx, sy = start; gx, gy = goal
        q = collections.deque([(sx, sy)])
        parent = { (sx, sy): None }
        while q:
            x, y = q.popleft()
            if (x, y) == (gx, gy):
                break
            for nx, ny in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
                if 0 <= nx < self.cols and 0 <= ny < self.rows:
                    if (nx, ny) not in parent:
                        parent[(nx, ny)] = (x, y)
                        q.append((nx, ny))
        if (gx, gy) not in parent: return None
        # reconstruct
        path = []
        cur = (gx, gy)
        while cur is not None:
            path.append(cur)
            cur = parent[cur]
        path.reverse()
        return path

    def _clearance_halo_along_path(self, path):
        c = max(self.clearance, CORRIDOR_WIDTH - 1)
        for (x, y) in path:
            for yy in range(max(0, y - c), min(self.rows, y + c + 1)):
                for xx in range(max(0, x - c), min(self.cols, x + c + 1)):
                    if self.map[yy][xx] != SPAWN:
                        self.map[yy][xx] = WALKABLE

    def mutate(self, rng):
        op = rng.choices(
            ["add_element", "remove_area", "shift_area", "bush_patch"],
            weights=[0.40, 0.20, 0.25, 0.15],
            k=1
        )[0]

        if op == "add_element":
            choice = rng.random()
            if choice < 0.25:
                self._try_stamp_line_half(rng, WATER, min_len=8, max_len=20, thickness=rng.randint(1,2))
            elif choice < 0.55:
                self._try_stamp_rect_half(rng, WALL, w=rng.randint(3,7), h=rng.randint(3,7))
            elif choice < 0.80:
                self._try_stamp_blob_half(rng, COVER, radius=rng.randint(2,4), p=0.6)
            else:
                self._try_stamp_rect_half(rng, BOX, w=rng.randint(1,3), h=rng.randint(1,3))

        elif op == "remove_area":
            # randomly wipe a small rect on half (acts like cleanup)
            y0, y1, x0, x1 = self._half_bounds()
            w, h = rng.randint(2,6), rng.randint(2,6)
            x = rng.randint(x0, max(x0, x1 - w + 1))
            y = rng.randint(y0, max(y0, y1 - h + 1))
            for yy in range(y, y+h):
                for xx in range(x, x+w):
                    if self.map[yy][xx] in OBSTACLE:
                        self.map[yy][xx] = WALKABLE

        elif op == "shift_area":
            # pick a small rect, clear it, and re-stamp nearby
            y0, y1, x0, x1 = self._half_bounds()
            w, h = rng.randint(3,6), rng.randint(3,6)
            sx = rng.randint(x0, max(x0, x1 - w + 1))
            sy = rng.randint(y0, max(y0, y1 - h + 1))
            tiles = []
            for yy in range(sy, sy+h):
                for xx in range(sx, sx+w):
                    tiles.append(self.map[yy][xx])
                    if self.map[yy][xx] in OBSTACLE:
                        self.map[yy][xx] = WALKABLE
            # try to restamp something coherent
            if rng.random() < 0.5:
                self._try_stamp_rect_half(rng, WALL, w=w, h=h)
            else:
                self._try_stamp_blob_half(rng, COVER, radius=max(2, min(w, h)//2), p=0.6)

        else:  # bush_patch
            self._try_stamp_blob_half(rng, BUSH, radius=rng.randint(3,6), p=0.7)

        # Re-impose symmetry & ensure connectivity after mutation
        self._reimpose_symmetry()
        self._ensure_spawn_connectivity()

    def crossover(self, other, rng):
        child = BrawlStarsMap(size=(self.rows, self.cols),
                              symmetry_axis=self.symmetry_axis,
                              clearance=self.clearance)
        split_point = rng.randint(0, self.cols - 1)
        for y in range(self.rows):
            for x in range(self.cols):
                child.map[y][x] = self.map[y][x] if x <= split_point else other.map[y][x]
        child._repair_spawns(rng)
        # Make the child symmetric and connected
        child._reimpose_symmetry()
        child._ensure_spawn_connectivity()
        return child

    def _repair_spawns(self, rng):
        spawns = get_positions(self.map, SPAWN)  # list of (y, x)
        # Clamp to 10; if too many remove extras farthest from center
        while len(spawns) > 10:
            y, x = spawns.pop()
            self.map[y][x] = WALKABLE
        # Add missing in symmetric pairs on half
        while True:
            spawns = get_positions(self.map, SPAWN)
            if len(spawns) >= 10:
                break
            y0, y1, x0, x1 = self._half_bounds()
            x = rng.randint(x0+2, x1-2)
            y = rng.randint(y0+2, y1-2)
            if self.map[y][x] == WALKABLE:
                self.map[y][x] = SPAWN
                self._reimpose_symmetry()



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
            if rng.random() < 0.99:  # mutation rate
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