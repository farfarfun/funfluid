import math
import os

import pandas as pd


class BaseProject:
    """椭圆粒子仿真算例目录的访问入口。

    封装一个算例目录下的取向数据文件枚举、输出目录创建与原始数据解析。
    """

    def __init__(self, path: str) -> None:
        """
        Args:
            path: 算例根目录，目录下存放 `orientation*` 原始数据文件。
        """
        self.path = path

    @staticmethod
    def _load(path: str, index: int = 0, angle_unit: int = 1) -> pd.DataFrame:
        """读取单个取向数据文件并归一化列名与角度单位。

        Args:
            path: 取向数据文件路径，列之间以任意数量空白分隔、无表头。
            index: 写入 `index` 列的算例序号，用于多算例合并后区分来源。
            angle_unit: 原始 `theta` 列的单位。`1` 表示角度（度），
                其余值表示以 π 为单位的归一化角。

        Returns:
            含 `x`/`y`/`theta`/`step`/`index` 等列的 DataFrame，
            `theta` 已统一换算为弧度。
        """
        df = pd.read_csv(path, sep=r"\s+", header=None)
        cols = [f"c{i}" for i in df.columns]
        cols[0] = "x"
        cols[1] = "y"
        cols[4] = "theta"
        cols[11] = "step"
        df.columns = cols
        if angle_unit == 1:
            df["theta"] = df["theta"] * math.pi / 180.0
        else:
            df["theta"] = df["theta"] * math.pi
        df["step"] = df["step"].astype("int")
        df["index"] = index
        return df

    @property
    def orientation_files(self) -> list[str]:
        """算例目录下所有 `orientation` 开头的数据文件路径，按文件名升序排列。"""
        results = [
            os.path.join(self.path, file)
            for file in os.listdir(self.path)
            if file.startswith("orientation")
        ]
        results.sort()
        return results

    def output_path(self, sub_path: str = "") -> str:
        """返回算例的输出目录，目录不存在时自动创建。

        Args:
            sub_path: 相对于 `<算例目录>/output/` 的子目录名，默认为输出根目录。

        Returns:
            已存在（或刚创建）的输出目录路径。
        """
        path = os.path.join(self.path, "output", sub_path)
        os.makedirs(path, exist_ok=True)
        return path

    @property
    def project_name(self) -> str:
        """算例名称，即算例目录的目录名。"""
        return os.path.basename(self.path)
