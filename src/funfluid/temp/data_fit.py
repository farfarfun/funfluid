import numpy as np
from scipy.optimize import curve_fit


def func(x, a, b):
    return 10 ** (a * x + b)


def func2(x, a, b):
    return a * (23.16 * x) ** b


class DataFit:
    def __init__(self, ls=23.16, b1=1.17 * 10**-5):
        self.ls = ls
        self.b1 = b1

    def fit_init(self, data, start_index=0, end_index=0):
        d2 = np.array(
            [
                [float(i) for i in line.split("\t")]
                for line in data.split("\n")
                if len(line) > 0
            ]
        )
        if end_index == 0:
            return d2[start_index:, 0], d2[start_index:, 1]
        else:
            return d2[start_index:end_index, 0], d2[start_index:end_index, 1]

    def fit_line(self, data, start_index=1, end_index=-1):
        xd, yd = self.fit_init(data, start_index, end_index)
        x, _ = self.fit_init(data)

        (k, b), _ = curve_fit(func, np.array(xd), np.array(yd))
        y = 10 ** (x * k + b)
        return (k, b), y

    def fit_exp(self, data, start_index=1, end_index=-1):
        xd, yd = self.fit_init(data, start_index, end_index)
        x, _ = self.fit_init(data)

        (k, b), _ = curve_fit(func2, np.array(xd), np.array(yd))
        y = k * ((self.ls * x) ** b)
        return (k, b), y


def fit(data):
    fit = DataFit()
    xd, yd = fit.fit_init(data)
    (k1, b1), y1 = fit.fit_line(data)
    (k2, b2), y2 = fit.fit_exp(data)

    d4 = np.transpose(np.array([xd, yd, y1, y2]))
    return (k1, b1, k2, b2), d4
