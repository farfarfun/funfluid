import numpy as np
import pandas as pd
from tqdm import tqdm


def msd_straight_forward(arr):
    shifts = np.arange(len(arr))
    msds = np.zeros(shifts.size)
    for i, shift in enumerate(shifts):
        diffs = arr[: -shift if shift else None] - arr[shift:]
        dist = np.square(diffs).sum(axis=1)
        msds[i] = dist.mean()
    return msds


def auto_corr_fft(x):
    N = len(x)
    F = np.fft.fft(x, n=2 * N)
    PSD = F * F.conjugate()
    res = np.fft.ifft(PSD)
    res = (res[:N]).real
    n = N * np.ones(N) - np.arange(0, N)
    return res / n


def msd_fft(arr):
    N = len(arr)
    D = np.square(arr).sum(axis=1)
    D = np.append(D, 0)
    S2 = sum([auto_corr_fft(arr[:, i]) for i in range(arr.shape[1])])
    Q = 2 * D.sum()
    S1 = np.zeros(N)
    for m in tqdm(range(N)):
        Q = Q - D[m - 1] - D[N - m]
        S1[m] = Q / (N - m)
    return S1 - 2 * S2


def cul_msd(df, col_time="t", col_x="x", col_y="y"):
    df_fill = pd.DataFrame([[i + 1] for i in range(1, int(df[col_time].max()))])

    df_fill.columns = [col_time]
    df_fill = pd.merge(df_fill, df, on=col_time, how="left")

    # msd_result = []
    # for i in tqdm(df_fill[col_time].drop_duplicates().values):
    #     df_fill["x1"] = df_fill[col_x].diff(i)
    #     df_fill["y1"] = df_fill[col_y].diff(i)
    #     df_fill["T"] = df_fill["x1"] ** 2 + df_fill["y1"] ** 2
    #     msd_result.append([i, df_fill["T"].sum(), df_fill["T"].count()])
    # msd_df = pd.DataFrame(msd_result)
    arr = df_fill[[col_x, col_y]].values
    msd_df = df_fill[[col_time]].copy()
    msd_df["msd"] = msd_fft(arr)

    msd_df = msd_df[msd_df["msd"] > 0]
    msd_df = msd_df.reset_index(drop=True)
    msd_df["v"] = np.sqrt(msd_df["msd"]) / msd_df[col_time]
    msd_df = msd_df[msd_df["step"] > 0]
    return msd_df
