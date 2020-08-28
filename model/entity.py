from typing import Any, Dict, Tuple
from grid import Grid


class Driver:
    def __init__(self, od: Dict[str, Any]):
        self.driver_id = od['driver_id']  # type: str
        self.loc = od['driver_location']  # type: Tuple[float, float]
        self.grid, self.grid_no = Grid.find_grid(od['driver_location'][0], od['driver_location'][1])


class Order:
    def __init__(self, od: Dict[str, Any]):
        self.order_id = od['order_id']  # type: str
        self.start_time = od['timestamp']  # type: int
        self.start_loc = od['order_start_location']  # type: Tuple[float, float]
        self.start_grid, self.start_grid_no = Grid.find_grid(od['order_start_location'][0], od['order_start_location'][1])

        self.finish_time = od['order_finish_timestamp']  # type: int
        self.finish_loc = od['order_finish_location']  # type: Tuple[float, float]
        self.finish_grid, self.finish_grid_no = Grid.find_grid(od['order_finish_location'][0], od['order_finish_location'][1])

        self.day_of_week = od['day_of_week']  # type: int
        self.reward = od['reward_units']  # type: float


class Pair:
    def __init__(self, od: Dict[str, Any]):
        self.driver_id = od['driver_id']  # type: str
        self.order_id = od['order_id']  # type: str
        self.od_distance = od['order_driver_distance']  # type: float
        self.pick_up_eta = od['pick_up_eta']  # type: float
        self.weight = od['reward_units']
        self.duration = od['order_finish_timestamp'] - od['timestamp']

    def redefine_weight(self, score):
        self.weight = score
