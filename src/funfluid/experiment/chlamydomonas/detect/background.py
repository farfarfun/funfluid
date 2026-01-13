import pickle
from typing import List

import numpy as np

from funfluid.common.base.cache import BaseCache
from funfluid.experiment.chlamydomonas.base.base import process_wrap, VideoBase
from funfluid.utils.log import logger


class BackGround:
    def __init__(self, length, width, height=3, uid=None):
        self.back_image = np.zeros([width, length, height])
        self.count = 0
        self.uid = uid

    def add(self, image):
        if self.count == 0:
            self.count += 1
            self.back_image = image
            return
            # self.back_image = self.back_image * self.count + image
        self.count += 1
        # self.back_image /= self.count
        self.back_image = np.max(np.array([self.back_image, image]), axis=0)
        return self

    def valid(self, image, s1=0.4, s2=0.03):
        if self.count == 0:
            return True

        res1 = np.abs(self.back_image.astype(np.int32) - image.astype(np.int32))
        res = abs(np.sum(res1 > (image.max() - image.min()) * s1))
        if 1.0 * res / image.shape[0] / image.shape[1] < s2:
            return True
        return False

    def score(self, image):
        res1 = np.abs(self.back_image.astype(np.int32) - image.astype(np.int32))
        return np.sum(res1 > 30)

    def __str__(self):
        return f"{self.uid}    {self.count}    {self.back_image.shape}"


class BackGroundDetect(BaseCache):
    def __init__(self, config: VideoBase, *args, **kwargs):
        super(BackGroundDetect, self).__init__(
            filepath=f"{config.cache_dir}/detect_backgrounds.pkl", *args, **kwargs
        )
        self.config = config
        self.background_list: List[BackGround] = []

    def process_background_nearest(
        self, image, debug=False, *args, **kwargs
    ) -> BackGround:
        back = None
        min_score = 9999999999990
        for back in self.background_list[::-1]:
            score = back.score(image)
            if score < min_score:
                min_score = score
                back = back
        return back

    def process_background_image(
        self, step, image, debug=False, *args, **kwargs
    ) -> BackGround:
        for back in self.background_list[::-1]:
            if back.valid(image):
                back.add(image)
                return back
        back = BackGround(self.config.video_width, self.config.video_height, uid=step)
        back.add(image)
        self.background_list.append(back)
        logger.debug("add a newer")
        return back

    def execute(self, *args, **kwargs):
        def fun(step, image, ext_json):
            self.process_background_image(step, image)
            return len(self.background_list)

        process_wrap(fun, self.config, desc="detect background")

    def _read(self, *args, **kwargs):
        with open(self.filepath, "rb") as fr:
            self.background_list = pickle.load(fr)

    def _save(self, *args, **kwargs):
        with open(self.filepath, "wb") as fw:
            pickle.dump(self.background_list, fw)
