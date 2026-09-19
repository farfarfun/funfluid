import math


import numpy as np


class Buff:
    def __init__(self, name, dt, obs_cv_ct, obs_cv_nb, output_dir):
        self.name = name
        self.buff = np.zeros([2])
        self.avg1_buff = np.zeros([2])
        self.avg2_buff = np.zeros([2])
        self.avg3_buff = np.zeros([2])
        self.it = 0
        self.dt = dt
        self.output_dir = output_dir
        self.freq = 1.0
        self.obs = 0.0
        self.obs_cv_ct = obs_cv_ct
        self.obs_cv_nb = obs_cv_nb
        self.obs_cv_cnt = 0
        self.obs_cv = False

    # Add a value to the buffer

    def add(self, value):
        self.buff = np.append(self.buff, value)
        self.it += 1

    # Full average buffer
    def f_avg(self):
        return np.sum(self.buff) / len(self.buff)

    # Partial average buffer
    @staticmethod
    def p_avg(buff, i, j):
        return np.sum(buff[i:j]) / (float(j - i + 1))

    # Compute average of moving average
    def mv_avg(self):
        # f_avg = self.f_avg()
        it_s = math.floor(3 * self.it / 4)
        it_e = self.it
        self.obs = self.p_avg(self.buff, it_s, it_e)
        self.avg1_buff = np.append(self.avg1_buff, self.obs)
        self.obs = self.p_avg(self.avg1_buff, it_s, it_e)
        self.avg2_buff = np.append(self.avg2_buff, self.obs)
        self.obs = self.p_avg(self.avg2_buff, it_s, it_e)
        self.avg3_buff = np.append(self.avg3_buff, self.obs)
        self.obs = self.p_avg(self.avg3_buff, it_s, it_e)

        growth = 0.0
        # 注意：avg3_buff 按 mv_avg() 调用次数增长，而不是按 add() 调用
        # 次数（self.it）增长，两者在调用方不同步时并不相等。之前按 self.it
        # 判断会在 avg3_buff 长度不足 5 时触发 IndexError，这里改为直接
        # 判断 avg3_buff 自身的长度。
        if len(self.avg3_buff) > 5:
            growth = (self.avg3_buff[-1] - self.avg3_buff[-5]) / (4.0 * self.dt)

            if abs(growth) < self.obs_cv_ct:
                self.obs_cv_cnt += 1
            else:
                self.obs_cv_cnt = 0
            if self.obs_cv_cnt > self.obs_cv_nb:
                self.obs_cv = True

        return self.obs, growth
