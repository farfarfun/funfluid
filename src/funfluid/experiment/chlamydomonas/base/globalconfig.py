import os


class VideoSplit:
    def __init__(self):
        self.video_name = ""
        self.video_paths = []
        self.cache_dir = ""
        self.config_path = ""

    def parse_path(self, video_path):
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

    def parse_other(self):
        self.config_path = f"{os.path.splitext(self.video_paths[0])}.json"

    def to_json(self):
        return {
            "video_name": self.video_name,
            "video_path": ",".join(self.video_paths),
            "config_path": self.config_path,
            "cache_dir": self.cache_dir,
        }


class GlobalConfig:
    def __init__(self, path_root):
        # 总得路径
        self.path_root = path_root
        # 视频路径
        self.videos_dir = f"{self.path_root}/videos"
        # 结果保持位置
        self.results_dir = f"{self.path_root}/results"
        # 总的结果文件
        self.results_json = f"{self.path_root}/result.json"

    def get_result_path(self, video_path):
        splits = VideoSplit()
        if not splits.parse_path(video_path):
            return None
        splits.parse_other()
        splits.cache_dir = splits.cache_dir.replace(self.videos_dir, self.results_dir)
        return splits
