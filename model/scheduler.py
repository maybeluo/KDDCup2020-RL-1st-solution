import math
from typing import Dict, List, Any, Tuple
from grid import Grid
from matcher import Matcher
from global_var import SPEED, REPO_NAIVE


class Scheduler:
    def __init__(self, gamma: float):
        self.gamma = gamma

    def reposition(self, matcher: Matcher, repo_observ: Dict[str, Any]) -> List[Dict[str, str]]:
        if REPO_NAIVE:
            return Scheduler.reposition_naive(repo_observ)
        timestamp, day_of_week, drivers = Scheduler.parse_repo(repo_observ)
        grid_ids = matcher.get_grid_ids()

        reposition = []  # type: List[Dict[str, str]]
        for driver_id, current_grid_id in drivers:
            current_value = matcher.get_grid_value(current_grid_id)
            best_grid_id, best_value = current_grid_id, 0
            for grid_id in grid_ids:
                time = Grid.mahattan_distance(current_grid_id, grid_id) / SPEED
                discount = math.pow(self.gamma, time)
                proposed_value = matcher.get_grid_value(grid_id)
                incremental_value = discount * proposed_value - current_value
                if incremental_value > best_value:
                    best_grid_id, best_value = grid_id, incremental_value
            reposition.append(dict(driver_id=driver_id, destination=best_grid_id))
        return reposition

    @staticmethod
    def reposition_naive(repo_observ):
        repo_action = []
        for driver in repo_observ['driver_info']:
            # the default reposition is to let drivers stay where they are
            repo_action.append({'driver_id': driver['driver_id'], 'destination': driver['grid_id']})
        return repo_action

    @staticmethod
    def parse_repo(repo_observ):
        timestamp = repo_observ['timestamp']  # type: int
        day_of_week = repo_observ['day_of_week']  # type: int
        drivers = []  # type: List[Tuple[str, str]]
        for driver in repo_observ['driver_info']:
            drivers.append((driver['driver_id'], driver['grid_id']))
        return timestamp, day_of_week, drivers
