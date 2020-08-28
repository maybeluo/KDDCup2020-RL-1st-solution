import collections
from typing import Dict, List, Set, Tuple, Any
import sys
import pickle
import ctypes
import numpy as np
import math
from utils import get_path, get_topK, rehash, rebuild_by_score, build_graph, get_pairs, finish_prob, get_layer_id, discrete_time
from entity import Pair, Driver, Order
from global_var import lng_step, lat_step, DIRS, DIR_NUM, NUM_TOPK, TIME_INTERVAL, IS_CLEAR


class Matcher:
    def __init__(self, alpha, gamma):
        self.alpha = alpha
        self.gamma = gamma
        self.dow = -1
        self.cur_discrete_time = 0
        self.grid_values = collections.defaultdict(float)
        # tile coding
        self.layer_values = collections.defaultdict(float)
        if sys.platform != 'darwin':
            self.hung = ctypes.cdll.LoadLibrary(get_path(__file__, "hungnp.so"))
        else:
            self.hung = ctypes.cdll.LoadLibrary(get_path(__file__, "hungnpmc.so"))
        self.hung.MaxProfMatching.restype = ctypes.c_double

    def dispatch(self, dispatch_observ: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        if len(dispatch_observ) == 0:
            return []
        self.cur_discrete_time = discrete_time(dispatch_observ[0]['timestamp'])
        if self.dow != dispatch_observ[0]['day_of_week']:
            self.dow = dispatch_observ[0]['day_of_week']
            if IS_CLEAR:
                self.grid_values = collections.defaultdict(float)
                self.layer_values = collections.defaultdict(float)
        drivers, orders, pairs = Matcher.parse_dispatch(dispatch_observ)
        edges = []  # type: List[Pair]
        for key in pairs:  # type: str
            pair = pairs[key]  # type: Pair
            order = orders[pair.order_id]
            driver = drivers[pair.driver_id]
            duration = int(1. * pair.duration / TIME_INTERVAL)
            duration = max(1, duration)
            v0 = self.get_smoothed_value(driver.loc, driver.grid)
            v1 = self.get_smoothed_value(order.finish_loc, order.finish_grid)
            done_prob = finish_prob(pair.od_distance, order.start_loc, order.finish_loc, order.start_time)

            if done_prob > 0:
                gamma = math.pow(self.gamma, duration)
                complete_update = order.reward + gamma * v1 - v0
                cancel_update = gamma * v0 - v0
                expected_update = done_prob * complete_update
                pair.redefine_weight(expected_update)
                edges.append(pair)

        # Assign drivers
        assigned_driver_ids = set()  # type: Set[str]

        # begin hungary
        driver_order_to_score = dict()
        for each in edges:
            driver_order_to_score[str(each.driver_id) + '#' + str(each.order_id)] = each.weight
        dispatch_observ = rebuild_by_score(edges)
        dispatch_observ = get_topK(dispatch_observ, NUM_TOPK)
        dispatch = self.hungary(dispatch_observ)
        for each in dispatch:
            assigned_driver_ids.add(each['driver_id'])
            driver = drivers[each['driver_id']]
            key = str(each['driver_id']) + '#' + str(each['order_id'])
            if key in driver_order_to_score:
                score = driver_order_to_score[key]
                self.update_value(driver.loc, driver.grid, self.alpha * score)

        for driver in drivers.values():
            if driver.driver_id in assigned_driver_ids:
                continue
            v0 = self.get_smoothed_value(driver.loc, driver.grid)
            v1 = v0
            update = self.gamma * v1 - v0  # no reward
            self.update_value(driver.loc, driver.grid, self.alpha * update)

        return dispatch

    def hungary(self, dispatch_observ):
        if len(dispatch_observ) == 0:
            return []
        driver_id_orig2new, order_id_orig2new, driver_id_new2orig, order_id_new2orig = rehash(dispatch_observ)
        costs, row_is_driver = build_graph(dispatch_observ, driver_id_orig2new, order_id_orig2new)
        n = len(costs)
        m = len(costs[0])
        lmate = -np.ones(n, dtype=np.int32)
        lmate = lmate.ctypes.data_as(ctypes.c_void_p)
        dataptr = costs.ctypes.data_as(ctypes.c_void_p)
        self.hung.MaxProfMatching(dataptr, n, m, lmate)
        array_pointer = ctypes.cast(lmate, ctypes.POINTER(ctypes.c_int * n))
        np_arr = np.frombuffer(array_pointer.contents, dtype=np.int32, count=n)
        lmate = np_arr.reshape((n,))
        lmate = list(lmate)
        dispatch_action = get_pairs(lmate, row_is_driver, driver_id_new2orig, order_id_new2orig)
        return dispatch_action

    def get_grid_ids(self) -> Set[str]:
        return set(self.grid_values.keys())

    def get_grid_value(self, grid_id: str) -> float:
        return self.grid_values[grid_id]

    def get_smoothed_value(self, loc: Tuple[float, float], grid_id: str) -> float:
        value = self.grid_values[grid_id]
        for i, one_dir in enumerate(DIRS):
            # all tiles share state if they are the same, regardless of their directions
            layer_id = get_layer_id(loc[0] + one_dir[0] * lng_step, loc[1] + one_dir[1] * lat_step, direction = 0)
            value += self.layer_values[layer_id]
        return value / (1 + DIR_NUM)

    def update_value(self, loc: Tuple[float, float], grid_id: str, delta: float) -> None:
        self.grid_values[grid_id] += delta
        for i, one_dir in enumerate(DIRS):
            # all tiles share state if they are the same, regardless of their directions
            layer_id = get_layer_id(loc[0] + one_dir[0] * lng_step, loc[1] + one_dir[1] * lat_step, direction = 0)
            self.layer_values[layer_id] += delta

    @staticmethod
    def parse_dispatch(dispatch_observ: List[Dict[str, Any]]) -> (Dict[str, Driver], Dict[str, Order], Dict[str, Set[Pair]]):
        drivers = collections.OrderedDict()  # type: collections.OrderedDict[str, Driver]
        orders = collections.OrderedDict()  # type: collections.OrderedDict[str, Order]
        pairs = collections.OrderedDict()  # type: collections.OrderedDict[str, Pair]
        for pair_raw in dispatch_observ:
            driver = Driver(pair_raw)
            drivers[driver.driver_id] = driver
            order = Order(pair_raw)
            orders[order.order_id] = order
            key = str(order.order_id) + "#" + str(driver.driver_id)
            pairs[key] = Pair(pair_raw)
        return drivers, orders, pairs
