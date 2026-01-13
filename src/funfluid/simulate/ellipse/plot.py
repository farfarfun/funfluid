import re
import time

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

data = open("data.txt", "r").read()
data = [re.sub(" +", "\t", line) for line in data.split("\n") if len(line) > 0]
data = [[float(i) for i in line.split("\t") if len(i) > 0] for line in data]

df = pd.DataFrame(data)
df.columns = [
    "step",
    "x1",
    "y1",
    "a1",
    "b1",
    "phi1",
    "theta1",
    "x2",
    "y2",
    "a2",
    "b2",
    "phi2",
    "theta2",
    "res",
    "",
    "o1x",
    "o1y",
    "o2x",
    "o2y",
]
print(df)


def plot_ellipse(x0, y0, a, b, phi, theta0, ox, oy):
    theta = np.arange(-2 * np.pi, 2 * np.pi, 0.01)
    x = x0 + a * np.cos(theta) * np.cos(phi) - b * np.sin(theta) * np.sin(phi)
    y = y0 + a * np.cos(theta) * np.sin(phi) + b * np.sin(theta) * np.cos(phi)

    x1 = x0 + a * np.cos(theta0) * np.cos(phi) - b * np.sin(theta0) * np.sin(phi)
    y1 = y0 + a * np.cos(theta0) * np.sin(phi) + b * np.sin(theta0) * np.cos(phi)
    plt.plot(x, y, "o")
    plt.plot(x1, y1, "o")
    plt.plot(ox, oy, "o")


def plot_step(row):
    plt.figure()
    plot_ellipse(
        row["x1"],
        row["y1"],
        row["a1"],
        row["b1"],
        row["phi1"],
        row["theta1"],
        row["o1x"],
        row["o1y"],
    )
    plot_ellipse(
        row["x2"],
        row["y2"],
        row["a2"],
        row["b2"],
        row["phi2"],
        row["theta2"],
        row["o2x"],
        row["o2y"],
    )

    plt.title(f"{row['step']}-{row['res']}")
    plt.show()

    time.sleep(1)


df.apply(lambda row: plot_step(row), axis=1)
