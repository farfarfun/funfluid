import numpy as np
import pandas as pd


def cul_phr(
    df: pd.DataFrame,
    col_x: str = "x",
    col_y: str = "y",
    cx: float = 0,
    cy: float = 0,
    dr: float = 0.1,
) -> pd.DataFrame:
    """计算二维粒子在同心环带中的归一化径向概率密度。

    Args:
        df: 包含二维坐标的粒子数据。
        col_x: x 坐标列名。
        col_y: y 坐标列名。
        cx: 圆心的 x 坐标。
        cy: 圆心的 y 坐标。
        dr: 环带宽度，必须大于零。

    Returns:
        包含半径、粒子数和归一化概率密度的 DataFrame。

    Raises:
        ValueError: ``dr`` 不大于零时抛出。
    """
    if dr <= 0:
        raise ValueError("dr 必须大于零")
    data = df.copy()
    data["r"] = np.sqrt((data[col_x] - cx) ** 2 + (data[col_y] - cy) ** 2)
    data["r"] = np.round(data["r"] / dr) * dr
    r_df = data.groupby(["r"])[col_x].count().reset_index()
    r_df.columns = ["r", "hr"]
    r_df = r_df[r_df["r"] > 0]
    r_df["phr"] = 1.0 * r_df["hr"] / (2 * np.pi * r_df["r"] * dr)
    r_df["phr"] = r_df["phr"] / r_df["phr"].sum()
    return r_df
