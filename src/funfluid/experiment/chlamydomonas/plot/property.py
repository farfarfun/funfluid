"""颗粒属性统计分析（一次性分析脚本，非包对外公开 API）。

历史上这个模块在 import 时直接调用一个从未定义过的 ``analyse(...)``，
import 即报 ``NameError``。这里先把调用收敛到显式入口下，
并把缺失的实现标记为 ``NotImplementedError``，避免 import 时崩溃；
真正的统计逻辑需要后续单独实现。
"""

import pandas as pd

# 设置显示全部行，不省略
pd.set_option("display.max_rows", 5000)
# 设置显示全部列，不省略
pd.set_option("display.max_columns", 500)


def analyse_property(video_path: str) -> None:
    """对指定视频对应的颗粒属性做统计分析。

    Args:
        video_path: 待分析视频文件的本地路径。

    Raises:
        NotImplementedError: 具体统计逻辑是历史遗留的一次性脚本，
            尚未补齐实现。
    """
    raise NotImplementedError(f"property.py 的颗粒属性统计逻辑尚未实现（video_path={video_path}）")


if __name__ == "__main__":
    analyse_property("/Volumes/ChenDisk/experiment/results/80ppm/1215.avi")
