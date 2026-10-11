import os

import pandas as pd


def load_v(path: str | os.PathLike[str]) -> pd.DataFrame:
    """读取 Tecplot 的结构化速度场数据文件。

    Args:
        path: Tecplot 数据文件路径。

    Returns:
        以文件变量名为列的数据框，坐标列 ``x``、``y`` 转为整数。

    Raises:
        FileNotFoundError: 文件不存在时抛出。
        KeyError: 文件缺少 ``I``、``J`` 或坐标列时抛出。
    """
    with open(path) as fr:
        row1 = fr.readline()
        row2 = fr.readline()
    parameter_map = dict(kv.strip().split("=") for kv in row2.strip("zone").split(","))

    df = pd.read_csv(
        path,
        skiprows=2,
        header=None,
        nrows=int(parameter_map["I"]) * int(parameter_map["J"]),
        sep=r"\s+",
    )

    cols = row1.strip("ZIBE").split("=")[1].strip().replace('"', "").split(",")
    cols = [col for col in cols if len(col) > 0]

    df.columns = cols
    df[["x", "y"]] = df[["x", "y"]].astype("int")
    return df


def load_p(path: str | os.PathLike[str]) -> pd.DataFrame:
    """读取 Tecplot 的点数据文件。

    Args:
        path: Tecplot 数据文件路径。

    Returns:
        以文件变量名为列的数据框。

    Raises:
        FileNotFoundError: 文件不存在时抛出。
        KeyError: 文件缺少 ``E`` 参数时抛出。
    """
    with open(path) as fr:
        row1 = fr.readline()
        row2 = fr.readline()
    parameter_map = dict(kv.strip().split("=") for kv in row2.split(","))
    df = pd.read_csv(path, skiprows=2, header=None, nrows=int(parameter_map["E"]) + 1, sep=r"\s+")
    df.columns = row1.split("=")[1].strip().replace('"', "").split(",")
    return df
