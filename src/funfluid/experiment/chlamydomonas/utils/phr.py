import numpy as np


def cul_phr(df, col_x="x", col_y="y", cx=0, cy=0, dr=0.1):
    df["r"] = np.sqrt((df[col_x] - cx) ** 2 + (df[col_y] - cy) ** 2)
    df["r"] = np.round(df["r"] / dr) * dr
    r_df = df.groupby(["r"])[col_x].count().reset_index()
    r_df.columns = ["r", "hr"]
    r_df = r_df[r_df["r"] > 0]
    r_df["phr"] = 1.0 * r_df["hr"] / (2 * np.pi * r_df["r"] * dr)
    r_df["phr"] = r_df["phr"] / r_df["phr"].sum()
    return r_df
