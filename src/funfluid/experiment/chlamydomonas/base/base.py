import json
import logging
import os
import pickle

import cv2
from tqdm import tqdm

from funfluid.common.base.cache import BaseCache
from funfluid.experiment.chlamydomonas.base.globalconfig import VideoSplit


class VideoBase(BaseCache):
    def __init__(
        self,
        video_split: VideoSplit,
        start_second=0,
        end_second=5 * 3600 * 1000,
        *args,
        **kwargs,
    ):
        self.video_split = video_split
        self.video_name = video_split.video_name
        self.video_paths = video_split.video_paths
        self.cache_dir = video_split.cache_dir
        super(VideoBase, self).__init__(
            filepath=f"{self.cache_dir}/base.pkl", *args, **kwargs
        )

        self.start_second = start_second
        self.end_second = end_second

        self.video_width = 0
        self.video_height = 0
        self.frame_count = 0
        self.load_config()

    def load_config(self):
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        config_path = self.video_split.config_path
        if not os.path.exists(config_path):
            return
        data = json.loads(open(config_path, "r").read())
        if "startSecond" in data.keys():
            self.start_second = data["startSecond"]
        if "endSecond" in data.keys():
            self.end_second = data["endSecond"]

    def execute(self, *args, **kwargs):
        step = 1

        for video_path in self.video_paths:
            camera = cv2.VideoCapture(video_path)
            self.video_width = int(camera.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.video_height = int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
            rate = camera.get(cv2.CAP_PROP_FPS)
            frame_counter = int(camera.get(cv2.CAP_PROP_FRAME_COUNT))
            pbar = tqdm(
                range(int(frame_counter / rate * 1000)),
                desc=os.path.basename(video_path),
            )

            while True:
                res, image = camera.read()
                if not res:
                    break
                step += 1
                millisecond = int(camera.get(cv2.CAP_OPENNI_DEPTH_MAP))
                if millisecond > 0:
                    pbar.update(millisecond - pbar.n)
            camera.release()
            pbar.close()

        self.frame_count = step

    def print(self):
        logging.info(f"config-second:{self.start_second}->{self.end_second}")

    def to_json(self):
        return {
            "video_height": self.video_height,
            "video_width": self.video_width,
            "frame_count": self.frame_count,
        }

    def _read(self, *args, **kwargs):
        with open(self.filepath, "rb") as fr:
            self.video_width = pickle.load(fr)
            self.video_height = pickle.load(fr)
            self.frame_count = pickle.load(fr)

    def _save(self, *args, **kwargs):
        with open(self.filepath, "wb") as fw:
            pickle.dump(self.video_width, fw)
            pickle.dump(self.video_height, fw)
            pickle.dump(self.frame_count, fw)


def process_wrap(fun, config: VideoBase, desc="process"):
    index = 0
    camera = cv2.VideoCapture(config.video_paths[index])
    for step in tqdm(range(1, config.frame_count + 5), desc=desc):
        res, image = camera.read()
        if not res:
            index += 1
            if index >= len(config.video_paths):
                break
            camera.release()
            camera = cv2.VideoCapture(config.video_paths[index])
            res, image = camera.read()

        image = cv2.GaussianBlur(image, (3, 3), 1)
        millisecond = int(camera.get(cv2.CAP_OPENNI_DEPTH_MAP))

        if millisecond < config.start_second * 1000:
            continue
        elif millisecond > config.end_second * 1000:
            break
        ext_json = {"millisecond": millisecond}
        fun(step, image, ext_json)
    camera.release()
