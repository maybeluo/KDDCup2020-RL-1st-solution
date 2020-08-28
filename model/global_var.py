alpha = 0.025
gamma1 = 0.9
residual = 0.09
gamma2 = gamma1 + residual
time_step = 2
lng_step = 0.003
lat_step = 0.003
GRID_NUM = 8519
DIRS = [[3, 1], [1, -3], [-3, -1], [-1, 3], [0, 0]]
DIR_NUM = len(DIRS)
SPEED = 3 * 2
INF = 1e12
REPO_NAIVE = True   # True: use naive reposition algorithm
QUICK = True       # True: use probability quick version

NUM_TOPK = 11

TIME_INTERVAL = 10 * 60

IS_CLEAR = True # clear up the values when day_of_week changes

