import numpy as np
import os
import pandas as pd
import random
import math
from global_var import QUICK


def acc_dist(lng1, lat1, lng2, lat2):
    delta_lat = (lat1 - lat2) / 2
    delta_lng = (lng1 - lng2) / 2
    arc_pi = 3.14159265359 / 180
    R = 6378137
    return 2 * R * math.asin(math.sqrt(math.sin(arc_pi * delta_lat) ** 2 + math.cos(arc_pi * lat1) * math.cos(arc_pi * lat2) * (math.sin(arc_pi * delta_lng) ** 2)))


def get_cancel_prob(od_distance, start_loc, finish_loc, timestamp):
    if QUICK:
        return 0.01 * math.exp(math.log(20)/2000. * od_distance)
    dest_distance = acc_dist(start_loc[0], start_loc[1], finish_loc[0], finish_loc[1])
    type1 = [0.01170420419107327, 0.011207019692459854, 0.011546449093435978, 0.01884863953849936, 0.02491680458581119,
             0.03516195815907564, 0.04086130456994513, 0.048299280067015636, 0.05361063371897413, 0.06108357592353861]
    type2 = [0.08593582973402296, 0.09519422058873243, 0.1017559777282097, 0.11247952637804468, 0.1257643815269181,
             0.15757382064280756, 0.18561752617526786, 0.21870050620163034, 0.25365262800365274, 0.28741045770387896]
    type3 = [0.20698865741088152, 0.25653585750468955, 0.28873054746716675, 0.3025450351782363, 0.3452418484052541,
             0.39487368752345364, 0.4442851417448408, 0.4919876854596625, 0.5838032553470912, 0.6622435844277653]
    prob = 0.
    while timestamp < 1477944000:
        timestamp += 86400
    time_id = int(((timestamp - 1477944000) % 86400) // 1800)
    slot = int(od_distance / 200.)
    slot = slot if slot <= 9 else 9
    if dest_distance > 20000.:
        prob = type1[slot]
    elif 10000. < dest_distance <= 20000.:
        if 0 <= time_id < 8:
            r = random.random() * 19.5
            if 0. <= r < 18.:
                prob = type1[slot]
            else:
                prob = type2[slot]
        else:
            r = random.random() * 19.
            if 0. <= r < 16.:
                prob = type1[slot]
            else:
                prob = type2[slot]
    else:
        r = random.random() * 20.
        if 0 <= time_id < 8:
            if 0. <= r < 18.:
                prob = type1[slot]
            elif 18. <= r < 19.5:
                prob = type2[slot]
            else:
                prob = type3[slot]
        else:
            if 0. <= r < 16.:
                prob = type1[slot]
            elif 16. <= r < 19.:
                prob = type2[slot]
            else:
                prob = type3[slot]
    if dest_distance <= 1000.:
        prob = 0.5
    return prob


def finish_prob(od_distance, start_loc, finish_loc, timestamp):
    return 1 - max(min(get_cancel_prob(od_distance, start_loc, finish_loc, timestamp), 1), 0)


def pnpoly(testx, testy, boundary):
    nvert = boundary.shape[0]
    c = 0
    i = 0
    j = nvert - 1
    vertx = boundary[:, 0]
    verty = boundary[:, 1]
    while i < nvert:
        if (((verty[i] > testy) != (verty[j] > testy)) and
                (testx < (vertx[j] - vertx[i]) * (testy - verty[i]) / (verty[j] - verty[i]) + vertx[i])):
            c = 1 ^ c
        j = i
        i = i + 1
    return c


def judge_area(lng, lat, boundary, fuzzy=False):
    boundary = np.array(boundary)
    [lng_max, lat_max] = np.amax(boundary, axis=0)
    [lng_min, lat_min] = np.amin(boundary, axis=0)
    if lng < lng_min or lng > lng_max or lat < lat_min or lat > lat_max:
        return False
    if fuzzy:
        return True
    else:
        c = pnpoly(lng, lat, boundary)
        if c == 1:
            return True
        else:
            return False


def discrete_location(lng, lat, kdtree, grids):
    _, ids = kdtree.query([lng, lat], k=8)
    for one_id in ids:
        if judge_area(lng, lat, grids[one_id][1]):
            return one_id
    return -1


def discrete_time(timestamp):
    tm = pd.Timestamp(timestamp, unit='s', tz='Asia/Shanghai')
    return int(tm.hour * 60 + tm.minute) // 10


def get_path(path, file_name):
    return os.path.join(os.path.dirname(os.path.abspath(path)), file_name)


def rehash(dispatch_observ):
    driver_id_orig2new = dict()
    order_id_orig2new = dict()
    driver_id_new2orig = list()
    order_id_new2orig = list()
    driver_cnt = 0
    order_cnt = 0
    for each in dispatch_observ:
        driver_id = each["driver_id"]
        if driver_id not in driver_id_orig2new:
            driver_id_orig2new[driver_id] = driver_cnt
            driver_id_new2orig.append(driver_id)
            driver_cnt += 1
        order_id = each["order_id"]
        if order_id not in order_id_orig2new:
            order_id_orig2new[order_id] = order_cnt
            order_id_new2orig.append(order_id)
            order_cnt += 1
    return driver_id_orig2new, order_id_orig2new, driver_id_new2orig, order_id_new2orig


def get_pairs(lmate, row_is_driver, driver_id_new2orig, order_id_new2orig):
    dispatch_action = []
    for i in range(len(lmate)):
        if lmate[i] != -1:
            if row_is_driver:
                dispatch_action.append(dict(order_id=order_id_new2orig[lmate[i]], driver_id=driver_id_new2orig[i]))
            else:
                dispatch_action.append(dict(order_id=order_id_new2orig[i], driver_id=driver_id_new2orig[lmate[i]]))
    return dispatch_action


def get_topK(dispatch_observ, k=10):
    order_to_dis_idx = dict()
    dispatch_observ_after_sift = []
    for i in range(len(dispatch_observ)):
        elem = dispatch_observ[i]
        if elem['order_id'] not in order_to_dis_idx:
            order_to_dis_idx[elem['order_id']] = []
        order_to_dis_idx[elem['order_id']].append((elem['order_driver_distance'], i))
    for key in order_to_dis_idx:
        order_to_dis_idx[key].sort()
        for j in range(min(k, len(order_to_dis_idx[key]))):
            dispatch_observ_after_sift.append(dispatch_observ[order_to_dis_idx[key][j][1]])
    return dispatch_observ_after_sift


def build_graph(dispatch_observ, driver_id_orig2new, order_id_orig2new):
    # assure row < colum
    driver_num = len(driver_id_orig2new)
    order_num = len(order_id_orig2new)
    row_is_driver = driver_num <= order_num
    if row_is_driver:
        costs = np.zeros([driver_num, order_num])
    else:
        costs = np.zeros([order_num, driver_num])
    for each in dispatch_observ:
        driver_new_id = driver_id_orig2new[each["driver_id"]]
        order_new_id = order_id_orig2new[each["order_id"]]
        if row_is_driver:
            costs[driver_new_id][order_new_id] = each['score']
        else:
            costs[order_new_id][driver_new_id] = each['score']
    return costs, row_is_driver


def rebuild_by_score(edges):
    dispatch_observ = []
    for pair in edges:
        elem = dict()
        elem['order_id'] = pair.order_id
        elem['driver_id'] = pair.driver_id
        elem['score'] = pair.weight
        elem['pick_up_eta'] = pair.pick_up_eta
        elem['order_driver_distance'] = pair.od_distance
        dispatch_observ.append(elem)
    return dispatch_observ


def get_layer_id(lng, lat, direction = 0):
    return f'{direction:02d}#{lng:.2f}#{lat:.2f}'

