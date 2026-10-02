"""颗粒轨迹 CSV 数据加载（一次性分析脚本，非包对外公开 API）。

历史上这个模块在 import 时直接读取写死的本机路径并 ``print``，
本机没有该路径时 import 即报错。现在把读取逻辑收敛成带类型标注的
函数，import 本身不再有任何副作用；需要查看数据时显式调用
``plot_particle_csv(...)`` 或以脚本方式运行本文件。
"""

import pandas as pd

from funfluid.utils.log import logger


def plot_particle_csv(csv_path: str) -> pd.DataFrame:
    """读取颗粒轨迹 CSV 文件并返回其内容。

    Args:
        csv_path: 颗粒轨迹 CSV 文件的本地路径。

    Returns:
        读取到的颗粒轨迹数据。

    Raises:
        FileNotFoundError: 当 ``csv_path`` 不存在时。
    """
    df = pd.read_csv(csv_path)
    logger.info(f"加载颗粒轨迹数据：{csv_path}，共 {len(df)} 行")
    return df


if __name__ == "__main__":
    plot_particle_csv(
        "/Volumes/ChenDisk/experiment/results/tap/11.23005.avi/particle_without_list.csv"
    )
