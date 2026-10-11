import numpy as np
import pandas as pd


def msd_straight_forward(arr: np.ndarray) -> np.ndarray:
    """直接计算轨迹各采样间隔的均方位移。

    Args:
        arr: 形状为 ``(N, D)`` 的轨迹坐标数组。

    Returns:
        长度为 ``N`` 的均方位移数组。
    """
    shifts = np.arange(len(arr))
    msds = np.zeros(shifts.size)
    for i, shift in enumerate(shifts):
        diffs = arr[: -shift if shift else None] - arr[shift:]
        dist = np.square(diffs).sum(axis=1)
        msds[i] = dist.mean()
    return msds


def auto_corr_fft(x: np.ndarray) -> np.ndarray:
    """使用 FFT 计算一维序列的自相关。

    Args:
        x: 一维数值序列。

    Returns:
        与输入等长的归一化自相关数组。
    """
    N = len(x)
    if N == 0:
        return np.array([])
    F = np.fft.fft(x, n=2 * N)
    PSD = F * F.conjugate()
    res = np.fft.ifft(PSD)
    res = (res[:N]).real
    n = N * np.ones(N) - np.arange(0, N)
    return res / n


def msd_fft(arr: np.ndarray) -> np.ndarray:
    """使用 FFT 计算多维轨迹的均方位移。

    Args:
        arr: 形状为 ``(N, D)`` 的数值坐标数组。

    Returns:
        长度为 ``N`` 的均方位移数组。

    Raises:
        ValueError: 输入不是二维坐标数组时抛出。
    """
    if arr.ndim != 2:
        raise ValueError("arr 必须是形状为 (N, D) 的二维数组")
    N = len(arr)
    if N == 0:
        return np.array([])
    D = np.square(arr).sum(axis=1)
    D = np.append(D, 0)
    S2 = sum([auto_corr_fft(arr[:, i]) for i in range(arr.shape[1])])
    Q = 2 * D.sum()
    S1 = np.zeros(N)
    for m in range(N):
        Q = Q - D[m - 1] - D[N - m]
        S1[m] = Q / (N - m)
    return S1 - 2 * S2


def cul_msd(
    df: pd.DataFrame, col_time: str = "t", col_x: str = "x", col_y: str = "y"
) -> pd.DataFrame:
    """计算二维粒子轨迹的均方位移及对应的表观速度。

    Args:
        df: 包含时间和二维坐标的轨迹数据。
        col_time: 时间列名。
        col_x: x 坐标列名。
        col_y: y 坐标列名。

    Returns:
        包含时间间隔、``msd`` 和 ``v`` 列的数据框；不足两条有效记录时返回空结果。

    Raises:
        KeyError: 所需列不存在时抛出。
    """
    columns = [col_time, col_x, col_y]
    missing = [column for column in columns if column not in df.columns]
    if missing:
        raise KeyError(f"缺少计算 MSD 所需的列: {missing}")

    trajectory = df.loc[:, columns].dropna().sort_values(col_time)
    if len(trajectory) < 2:
        return pd.DataFrame(columns=[col_time, "msd", "v"])

    time = trajectory[col_time].to_numpy()
    arr = trajectory[[col_x, col_y]].to_numpy(dtype=float)
    elapsed = time - time[0]
    msd = msd_fft(arr)
    valid = (elapsed > 0) & (msd > 0)
    result = pd.DataFrame({col_time: elapsed[valid], "msd": msd[valid]})
    result["v"] = np.sqrt(result["msd"]) / result[col_time]
    return result.reset_index(drop=True)
