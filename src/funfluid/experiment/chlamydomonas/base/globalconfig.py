"""chlamydomonas 实验的视频切分与全局路径配置。"""

import os


class VideoSplit:
    """解析分段录制视频的文件名，并聚合为一组可按顺序处理的视频路径。

    录制设备会把超过单文件时长上限的视频拆成
    ``<name>.split1.avi``、``<name>.split2.avi``、... 这样的多个文件；
    本类负责从任意一个分段文件名反推出同组全部分段文件，
    以及该组视频对应的缓存目录、配置文件路径。
    """

    def __init__(self) -> None:
        self.video_name: str = ""
        self.video_paths: list[str] = []
        self.cache_dir: str = ""
        self.config_path: str = ""

    def parse_path(self, video_path: str) -> bool:
        """解析单个视频文件路径，识别是否属于分段录制并收集同组分段。

        Args:
            video_path: 单个视频文件的路径。若该视频不是分段录制，
                会被视为独立的单个视频；若是分段录制，必须传入
                该组的第一段（``*.split1.<ext>``），否则返回 ``False``。

        Returns:
            解析成功返回 ``True``（此时 `video_name`/`video_paths`/
            `cache_dir` 均已填充）；传入的是非首段分段文件时返回 ``False``。
        """
        path1, suffix1 = os.path.splitext(video_path)
        path2, suffix2 = os.path.splitext(path1)
        if not suffix2.startswith(".split"):
            self.cache_dir = path1
            self.video_name = os.path.basename(path1)
            self.video_paths = [video_path]
            return True

        if suffix2 != ".split1":
            return False

        self.cache_dir = path2
        self.video_name = os.path.basename(path2)
        self.video_paths = []

        for i in range(1, 100):
            path = f"{path2}.split{i}.avi"
            if not os.path.exists(path):
                break
            self.video_paths.append(path)
        return True

    def parse_other(self) -> None:
        """根据已解析出的首个视频路径生成对应的配置文件路径。

        必须在 `parse_path` 成功返回之后调用，否则 `video_paths` 为空。
        """
        self.config_path = f"{os.path.splitext(self.video_paths[0])}.json"

    def to_json(self) -> dict:
        """导出为可序列化的字典。

        Returns:
            包含视频名、以逗号拼接的视频路径、配置文件路径与缓存目录的字典。
        """
        return {
            "video_name": self.video_name,
            "video_path": ",".join(self.video_paths),
            "config_path": self.config_path,
            "cache_dir": self.cache_dir,
        }


class GlobalConfig:
    """chlamydomonas 实验的全局路径配置。

    统一管理某次实验的根目录、视频目录、结果目录与汇总结果文件路径。
    """

    def __init__(self, path_root: str) -> None:
        """
        Args:
            path_root: 实验数据的根目录。
        """
        # 总得路径
        self.path_root = path_root
        # 视频路径
        self.videos_dir = f"{self.path_root}/videos"
        # 结果保持位置
        self.results_dir = f"{self.path_root}/results"
        # 总的结果文件
        self.results_json = f"{self.path_root}/result.json"

    def get_result_path(self, video_path: str) -> "VideoSplit | None":
        """将视频路径映射为对应的结果缓存目录。

        Args:
            video_path: `videos_dir` 下的某个视频文件路径。

        Returns:
            解析成功时返回 `VideoSplit`（其 `cache_dir` 已替换为
            `results_dir` 下的对应路径）；若 `video_path` 是分段录制中
            非首段的文件，返回 ``None``。
        """
        splits = VideoSplit()
        if not splits.parse_path(video_path):
            return None
        splits.parse_other()
        splits.cache_dir = splits.cache_dir.replace(self.videos_dir, self.results_dir)
        return splits
