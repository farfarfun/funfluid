# -*- coding: utf-8 -*-
import math
from functools import partial
from typing import List

import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def _load(path, index=0):
    df = pd.read_csv(path, sep="\s+", header=None)
    cols = [f"c{i}" for i in df.columns]
    cols[0] = "x"
    cols[1] = "y"
    cols[4] = "theta"
    cols[11] = "step"
    df.columns = cols
    df["theta"] = (df["theta"]) * math.pi
    # df = df.reset_index(names='step')
    df["step"] = df["step"].astype("int")

    df["index"] = index
    return df


class Canvas:
    def __init__(
        self, width=800, height=100, x_start=0, y_start=-0.5, aspect=1, scale=1
    ):
        self.width = width
        self.height = height
        self.x_start = x_start
        self.y_start = y_start
        self.aspect = aspect
        self.scale = scale

    def plot(self):
        plt.axis([self.x_start, self.width, self.y_start, self.height])
        plt.grid(True)

    def figure(self, ax):
        ax.set_xlim(self.x_start, self.x_start + self.width)
        ax.set_ylim(self.y_start, self.y_start + self.height)
        ax.set_aspect(self.aspect)


class EllipseTrack:
    def __init__(
        self, df, a=10, b=5, color=None, marker=None, line_width=1, *args, **kwargs
    ):
        if isinstance(df, str):
            self.df = _load(df)
        else:
            self.df = df

        self.a = a
        self.b = b
        self.color = color
        self.marker = marker
        self.line_width = line_width
        self.snapshot_steps = []
        self.lns = []

    def transform(self):
        self.df["xx"] = self.df["x"]
        self.df["x"] = self.df["y"]
        self.df["y"] = self.df["xx"]
        self.df["theta"] = self.df["theta"] - math.pi / 2

    @property
    def min_x(self):
        return self.df["x"].min()

    @property
    def max_x(self):
        return self.df["x"].max()

    @property
    def min_y(self):
        return self.df["y"].min()

    @property
    def max_y(self):
        return self.df["y"].max()

    @property
    def min_step(self):
        return self.df["step"].min()

    @property
    def max_step(self):
        return self.df["step"].max()

    def add_snapshot(self, step=0, color=None, marker=None, line_width=None):
        self.snapshot_steps.append(
            {
                "step": step,
                "color": color or self.color,
                "marker": marker or self.marker,
                "line_width": line_width or self.line_width,
            }
        )

    def plot_ref(self, canvas: Canvas):
        self.lns = []
        self.lns.append(
            plt.plot(
                [],
                [],
                color=self.color,
                marker=self.marker,
                linewidth=self.line_width,
                alpha=0.8,
            )[0]
        )
        self.lns.append(
            plt.plot(
                [], [], color=self.color, marker=self.marker, linewidth=self.line_width
            )[0]
        )

        for i, record in enumerate(self.snapshot_steps):
            self.lns.append(
                plt.plot(
                    [],
                    [],
                    color=record["color"],
                    marker=record["marker"],
                    linewidth=record["line_width"],
                )[0]
            )
        return self.lns

    def _get_ellipse_data(self, step, canvas: Canvas, *args, **kwargs):
        a, b = self.a, self.b
        tmp_df = self.df[self.df["step"] <= step].tail(1).reset_index(drop=True)
        x0, y0 = tmp_df["x"][0], tmp_df["y"][0]
        theta = tmp_df["theta"][0]
        phi = np.array([i / 100.0 * np.pi for i in range(-1, 201)])
        x = x0 + np.cos(theta) * a * np.cos(phi) - np.sin(theta) * b * np.sin(phi)
        y = (
            y0
            + (np.sin(theta) * a * np.cos(phi) + np.cos(theta) * b * np.sin(phi))
            / canvas.aspect
        )

        x[0] = x0
        y[0] = y0
        return x, y

    def plot_update(self, step, canvas: Canvas):
        tmp_df = self.df[self.df["step"] <= step]
        self.lns[0].set_data(tmp_df["x"], tmp_df["y"])
        self.lns[1].set_data(*self._get_ellipse_data(step=step, canvas=canvas))

        for i, record in enumerate(self.snapshot_steps):
            if record["step"] <= step:
                self.lns[i + 2].set_data(
                    *self._get_ellipse_data(record["step"], canvas=canvas)
                )
            else:
                self.lns[i + 2].set_data([], [])
        return self.lns

    def plot(self, canvas: Canvas = None, step=10):
        fig, ax = plt.subplots()
        self.plot_ref()
        ani = animation.FuncAnimation(
            fig=fig,
            func=self.plot_update,
            frames=[i for i in range(2, self.df["step"].max() - 2, step)],
            interval=100,
            # init_func=self.plot_ref,
            blit=True,
            repeat=False,
        )
        plt.show()
        # ani.save("a.gif", writer='imagemagick')


class FlowTrack:
    def __init__(self, canvas: Canvas = None):
        self.canvas = canvas
        self.ellipses: List[EllipseTrack] = []
        self.lns = []

    def set_canvas(self, canvas):
        self.canvas = canvas

    def transform(self):
        for ellipse in self.ellipses:
            ellipse.transform()

    @property
    def max_x(self):
        return max([ellipse.max_x for ellipse in self.ellipses])

    @property
    def min_x(self):
        return min([ellipse.min_x for ellipse in self.ellipses])

    @property
    def max_y(self):
        return max([ellipse.max_y for ellipse in self.ellipses])

    @property
    def min_y(self):
        return min([ellipse.min_y for ellipse in self.ellipses])

    @property
    def min_step(self):
        return min([ellipse.min_step for ellipse in self.ellipses])

    @property
    def max_step(self):
        return max([ellipse.max_step for ellipse in self.ellipses])

    def add_ellipse(self, ellipse: EllipseTrack, *args, **kwargs):
        self.ellipses.append(ellipse)

    def plot_ref(self, ax):
        self.canvas.figure(ax)
        for ellipse in self.ellipses:
            self.lns.extend(ellipse.plot_ref(self.canvas))

    def plot_update(self, step=10, title="", *args, **kwargs):
        for ellipse in self.ellipses:
            ellipse.plot_update(step=step, canvas=self.canvas)
        self.lns[-1].set_text(title.replace("{step}", str(step)))
        return self.lns

    def plot(
        self,
        min_step=2,
        max_step=None,
        step=10,
        title="",
        dpi=1000,
        gif_path="./trak.gif",
    ):
        min_step = max(min_step or self.min_step, self.min_step)
        max_step = min(max_step or self.max_step, self.max_step)
        fig, ax = plt.subplots(figsize=(12, 6))

        plt.grid(ls="--")
        font = {"fontfamily": "Times New Roman", "style": "italic"}
        plt.xlabel(r"x", **font)
        plt.ylabel(r"y", **font)
        plt.tick_params(labelsize=11, direction="in")

        def scale_x(temp, position):
            return temp / self.canvas.scale

        def scale_y(temp, position):
            return temp / self.canvas.scale - 0.5

        # ax.xaxis.set_major_formatter(FuncFormatter(scale_x))
        # ax.yaxis.set_major_formatter(FuncFormatter(scale_y))

        labels = ax.get_xticklabels() + ax.get_yticklabels()
        [label.set_fontname("Times New Roman") for label in labels]

        self.plot_ref(ax)
        self.lns.append(plt.title("", fontsize=12, **font))

        ani = animation.FuncAnimation(
            fig=fig,
            # func=self.plot_update,
            func=partial(self.plot_update, title=title),
            frames=[i for i in range(min_step, max_step, step)],
            interval=100,
            blit=False,
            repeat=False,
        )
        plt.show()
        savefig_kwargs = {"bbox_inches": "tight"}
        ani.save(
            gif_path,
            writer="imagemagick",
            # dpi=1000,
            savefig_kwargs=savefig_kwargs,
        )
        fig.savefig(gif_path.replace("gif", "png"), dpi=1000)
