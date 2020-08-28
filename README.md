# 1st solution for KDD Cup 2020 (RL track)
Competition link: https://outreach.didichuxing.com/competition/kddcup2020/

This is a joint work with people from BDA lab of BUAA (Yansheng Wang[team learder], Dingyuan Shi, Maoxiaomin Peng, Yi Xu, Yongxin Tong[coach]). Our solution focus on task 1: order dispatching. It consists of three steps:
1. build the bipartite graph and only keep top-K edges for each order;
2. run Hungarian algorithm for matching;
3. use **TD(0)** to update the state value.

Special thanks to the open source implementation of laxatives (https://github.com/laxatives/rl), your code helps me a lot.


## local test
clone the project and run the following coding with py3:
```python
python local_test.py
``` 