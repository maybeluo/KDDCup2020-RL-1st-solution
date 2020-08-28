import math
import pickle
from utils import get_path
from global_var import INF


class Grid:
    grids = pickle.load(open(get_path(__file__, "grids_info"), "rb"))
    grid_ids = pickle.load(open(get_path(__file__, "grid_id"), "rb"))
    kdtree = pickle.load(open(get_path(__file__, "kdtree"), "rb"))

    @staticmethod
    def find_grid(lng: float, lat: float) -> str:
        _, i = Grid.kdtree.query([lng, lat])
        return Grid.grid_ids[i], i

    @staticmethod
    def mahattan_distance(grid_hash0: str, grid_hash1: str) -> float:
        if grid_hash0 in Grid.grids and grid_hash1 in Grid.grids:
            lng0, lat0 = Grid.grids[grid_hash0]
            lng1, lat1 = Grid.grids[grid_hash1]
            delta_lng = 0.685 * abs(lng0 - lng1)
            delta_lat = abs(lat0 - lat1)
            return 111320 * math.sqrt(delta_lat * delta_lat + delta_lng * delta_lng)
        return INF
