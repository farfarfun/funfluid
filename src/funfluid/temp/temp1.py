"""路径扩展名拆分的小工具。

模块导入时不执行任何文件访问或输出；以脚本方式运行时才会打印示例结果。
"""

import os


def split_all_extensions(path: str) -> tuple[str, list[str]]:
    """反复拆分路径末尾的扩展名，直到不再含扩展名为止。

    用于处理 `a.tar.gz`、`video.001.avi` 这类多重后缀的文件名。

    Args:
        path: 待拆分的文件路径。

    Returns:
        二元组 `(stem, extensions)`：`stem` 是去掉全部扩展名后的路径，
        `extensions` 是按从左到右顺序排列的扩展名列表（含前导点号）。
    """
    extensions: list[str] = []
    stem = path
    while True:
        stem, ext = os.path.splitext(stem)
        if not ext:
            break
        extensions.insert(0, ext)
    return stem, extensions


if __name__ == "__main__":
    print(split_all_extensions("/c/d/a1/dfdf/sdfs.tar.gz"))
