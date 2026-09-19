import pandas as pd


def read_tecplot_point(path: str) -> pd.DataFrame:
    """读取 Tecplot 点数据（POINT 格式）文件，解析为 DataFrame。

    Args:
        path: Tecplot 数据文件路径，文件第一行为 `VARIABLES = ...` 变量列表，
            第二行为 `ZONE ...` 区域信息（包含节点数 `N`），从第三行起为数据本体。

    Returns:
        以变量名为列名的 DataFrame，行数等于 ZONE 中声明的节点数 `N`。
    """
    with open(path, "r") as f:
        data = f.read().split("\n")
    cols = [col for col in data[0].split("=")[1].strip().split(",")]
    zone = dict(
        [
            (kv.split("=")[0].strip(), kv.split("=")[1].strip())
            for kv in data[1].strip("ZONE").strip().split(",")
        ]
    )
    df = pd.read_csv(path, header=None, sep=r"\s+", nrows=int(zone["N"]), skiprows=2)
    df.columns = cols
    return df
