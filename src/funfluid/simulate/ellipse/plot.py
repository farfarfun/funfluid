"""椭圆粒子仿真结果的绘图工具。

模块导入时不产生任何文件读取、绘图或输出副作用；需要绘图时显式调用
`load_ellipse_frames` 与 `plot_frames`，或直接以脚本方式运行本模块。
"""

import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

#: `data.txt` 中每一列对应的字段名，顺序与仿真程序的输出一致。
ELLIPSE_COLUMNS: list[str] = [
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
    "reserved",
    "o1x",
    "o1y",
    "o2x",
    "o2y",
]


def load_ellipse_frames(path: str | Path = "data.txt") -> pd.DataFrame:
    """读取仿真输出的双椭圆轨迹文件。

    Args:
        path: 仿真输出文件路径，列之间以任意数量空格分隔。

    Returns:
        以 `ELLIPSE_COLUMNS` 命名的 DataFrame，每行是一个仿真步。

    Raises:
        FileNotFoundError: `path` 不存在。
        ValueError: 文件内容为空，或列数与 `ELLIPSE_COLUMNS` 不一致。
    """
    text = Path(path).read_text(encoding="utf-8")
    rows = [
        [float(value) for value in re.sub(" +", "\t", line).split("\t") if value]
        for line in text.split("\n")
        if line.strip()
    ]
    if not rows:
        raise ValueError(f"轨迹文件内容为空: {path}")

    df = pd.DataFrame(rows)
    if df.shape[1] != len(ELLIPSE_COLUMNS):
        raise ValueError(
            f"轨迹文件列数不匹配: 期望 {len(ELLIPSE_COLUMNS)} 列，实际 {df.shape[1]} 列"
        )
    df.columns = ELLIPSE_COLUMNS
    return df


def plot_ellipse(
    x0: float,
    y0: float,
    a: float,
    b: float,
    phi: float,
    theta0: float,
    ox: float,
    oy: float,
) -> None:
    """在当前 matplotlib 画布上绘制一个椭圆及其标记点。

    Args:
        x0: 椭圆中心横坐标。
        y0: 椭圆中心纵坐标。
        a: 椭圆长半轴长度。
        b: 椭圆短半轴长度。
        phi: 椭圆长轴相对 x 轴的旋转角（弧度）。
        theta0: 需要额外标记的椭圆参数角（弧度）。
        ox: 附加参考点横坐标。
        oy: 附加参考点纵坐标。
    """
    theta = np.arange(-2 * np.pi, 2 * np.pi, 0.01)
    x = x0 + a * np.cos(theta) * np.cos(phi) - b * np.sin(theta) * np.sin(phi)
    y = y0 + a * np.cos(theta) * np.sin(phi) + b * np.sin(theta) * np.cos(phi)

    x1 = x0 + a * np.cos(theta0) * np.cos(phi) - b * np.sin(theta0) * np.sin(phi)
    y1 = y0 + a * np.cos(theta0) * np.sin(phi) + b * np.sin(theta0) * np.cos(phi)
    plt.plot(x, y, "o")
    plt.plot(x1, y1, "o")
    plt.plot(ox, oy, "o")


def plot_step(row: pd.Series, show: bool = True) -> None:
    """绘制单个仿真步中两个椭圆的位置与姿态。

    Args:
        row: `load_ellipse_frames` 返回的 DataFrame 中的一行。
        show: 是否调用 `plt.show()` 立即展示；批量导出图片时传 `False`。
    """
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
    if show:
        plt.show()


def plot_frames(df: pd.DataFrame, show: bool = True) -> None:
    """逐行绘制轨迹文件中的所有仿真步。

    Args:
        df: `load_ellipse_frames` 返回的 DataFrame。
        show: 是否逐帧调用 `plt.show()`。
    """
    for _, row in df.iterrows():
        plot_step(row, show=show)


if __name__ == "__main__":
    import sys

    plot_frames(load_ellipse_frames(sys.argv[1] if len(sys.argv) > 1 else "data.txt"))
