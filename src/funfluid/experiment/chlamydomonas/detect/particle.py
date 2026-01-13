import os
import pickle
from typing import List

import cv2
import imageio
import numpy as np
import pandas as pd

from funfluid.common.base.cache import BaseCache
from funfluid.experiment.chlamydomonas.base.base import process_wrap, VideoBase
from funfluid.experiment.chlamydomonas.detect.background import (
    BackGroundDetect,
    BackGround,
)
from funfluid.experiment.chlamydomonas.detect.contain import ContainDetect, BackContain
from funfluid.utils.log import logger


def fit_particle(contour):
    if len(contour) < 50:
        logger.debug(f"size: {len(contour)}<50")
        return None, None, None
    area = round(cv2.contourArea(contour), 2)  # 获取轮廓面积
    if area < 100:
        logger.debug(f"area: {area} < 100")
        return None, None, None

    if len(contour) < 10:
        logger.debug(f"size: {len(contour)}<10")
        return None, None, None
    elif area > 100000:
        return None, None, None

    # (x,y) 代表椭圆中心点的位置, radius 代表半径
    center, radius, angle = cv2.fitEllipse(contour)
    s1 = 1 - abs(radius[0] * radius[1] * np.pi / 4 / area - 1)
    if s1 < 0.3:
        return None, None, None
    if radius[0] / radius[1] > 2 or radius[0] / radius[1] < 0.5:
        return None, None, None
    return center, radius, angle


class Particle:
    def __init__(
        self,
        contour,
        center,
        radius,
        angle,
        step,
        millisecond=None,
        background_uid=None,
        ext_json=None,
    ):
        ext_json = ext_json or {}
        self.contour = contour
        self.center = center
        self.radius = radius
        self.angle = angle
        self.step = step
        self.millisecond = millisecond or ext_json.get("millisecond", 0)
        self.background_uid = background_uid or ext_json.get("background_uid", 0)

    def to_json(self):
        return {
            "step": self.step,
            "centerX": self.center[0],
            "centerY": self.center[1],
            "radiusA": self.radius[0],
            "radiusB": self.radius[1],
            "angle": self.angle,
            "millisecond": self.millisecond,
            "background_uid": self.background_uid,
        }

    def parse(self, data):
        self.step = data["step"]
        self.center[0] = data["centerX"]
        self.center[1] = data["centerY"]
        self.radius[0] = data["radiusA"]
        self.radius[1] = data["radiusB"]
        self.angle = data["angle"]
        self.millisecond = data["millisecond"]
        self.background_uid = data["background_uid"]


class ParticleDetect(BaseCache):
    def __init__(self, config: VideoBase, *args, **kwargs):
        self.config = config
        super(ParticleDetect, self).__init__(
            filepath=f"{self.config.cache_dir}/detect_particles.pkl", *args, **kwargs
        )
        self.particle_csv_path = f"{self.config.cache_dir}/detect_particles.csv"
        self.particle_list: List[Particle] = []

    def process_particle_image(
        self, background: BackGround, contain: BackContain, image, step, ext_json
    ) -> List[Particle]:
        ext_json["background_uid"] = background.uid
        image = np.abs(background.back_image.astype(np.int32) - image.astype(np.int32))
        image = image.astype(np.uint8)

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  # 转为灰度值图
        # THRESH_OTSU, THRESH_TRIANGLE
        ret, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_TRIANGLE)  # 转为二值图
        # ret, binary = cv2.threshold(gray, img.max() * 0.92, 255, cv2.THRESH_BINARY)  # 转为二值图
        contours, hierarchy = cv2.findContours(
            binary, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE
        )  # 寻找轮廓

        particles = []
        for i, contour in enumerate(contours):
            center, radius, angle = fit_particle(contour)
            if center is None:
                continue
            if not contain.is_inside(center):
                continue

            particle = Particle(
                contour=contour,
                center=center,
                radius=radius,
                angle=angle,
                step=step,
                ext_json=ext_json,
            )
            self.particle_list.append(particle)
            particles.append(particle)
        return particles

    def _execute(
        self,
        backgrounds: BackGroundDetect,
        contains: ContainDetect,
        debug=False,
        *args,
        **kwargs,
    ):
        def fun(step, image, ext_json):
            background = backgrounds.process_background_nearest(image)
            contain = contains.find_contain(background.uid)
            particles = self.process_particle_image(
                background, contain, image, step, ext_json
            )
            if debug:
                cv2.circle(
                    image,
                    (int(contain.center[0]), int(contain.center[1])),
                    int(contain.radius),
                    (0, 255, 0),
                    2,
                )
                for particle in particles:
                    cv2.ellipse(
                        image,
                        (particle.center, particle.radius, particle.angle),
                        (0, 255, 0),
                        2,
                    )

                cv2.imshow(f"{self.config.video_name}", image)
                cv2.waitKey(delay=10)
            return len(self.particle_list)

        process_wrap(fun, self.config, desc="detect particle")

    def save_gif(
        self,
        backgrounds: BackGroundDetect,
        contains: ContainDetect,
        start=0,
        end=10,
        debug=False,
        *args,
        **kwargs,
    ):
        save_path = f"{self.config.cache_dir}/gifs"
        if not os.path.exists(save_path):
            os.mkdir(save_path)

        images = []

        def fun(step, image, ext_json):
            if step < start or step > end:
                return
            background = backgrounds.process_background_nearest(image)
            contain = contains.find_contain(background.uid)
            particles = self.process_particle_image(
                background, contain, image, step, ext_json
            )
            # cv2.circle(image, (int(contain.center[0]), int(contain.center[1])), int(contain.radius), (0, 255, 0), 2)
            for particle in particles:
                cv2.ellipse(
                    image,
                    (particle.center, particle.radius, particle.angle),
                    (0, 255, 0),
                    2,
                )

            if debug:
                cv2.imshow(f"{self.config.video_name}", image)
                cv2.waitKey(delay=10)

            if start < step <= end:
                images.append(image)
            if step == end:
                imageio.mimsave(
                    f"{save_path}/gif-{start}-{end}.gif", images, duration=0.8
                )
                images.clear()

            return len(self.particle_list)

        process_wrap(fun, self.config, desc="save gif")

    def save_image(
        self,
        backgrounds: BackGroundDetect,
        contains: ContainDetect,
        start=0,
        end=10,
        debug=False,
        *args,
        **kwargs,
    ):
        save_path = f"{self.config.cache_dir}/images"
        if not os.path.exists(save_path):
            os.mkdir(save_path)

        def fun(step, image, ext_json):
            if step < start or step > end:
                return
            background = backgrounds.process_background_nearest(image)
            contain = contains.find_contain(background.uid)
            particles = self.process_particle_image(
                background, contain, image, step, ext_json
            )
            for particle in particles:
                cv2.ellipse(
                    image,
                    (particle.center, particle.radius, particle.angle),
                    (0, 255, 0),
                    2,
                )
            if debug:
                cv2.imshow(f"{self.config.video_name}", image)
                cv2.waitKey(delay=10)
            imageio.imsave(f"{save_path}/image-{step}.png", image)

        process_wrap(fun, self.config, desc="save image")

    def save_video(
        self,
        backgrounds: BackGroundDetect,
        contains: ContainDetect,
        start=0,
        end=10,
        debug=False,
        *args,
        **kwargs,
    ):
        save_path = f"{self.config.cache_dir}/videos"
        if not os.path.exists(save_path):
            os.mkdir(save_path)

        # 该参数是MPEG-4编码类型，文件名后缀为.avi
        fourcc = cv2.VideoWriter_fourcc(*"XVID")
        # 设置视频帧频
        fps = 1000.0 / 60
        # 设置视频大小
        size = (self.config.video_width, self.config.video_height)
        out = cv2.VideoWriter(f"{save_path}/video-{start}-{end}.avi", fourcc, fps, size)

        def fun(step, image, ext_json):
            if step < start or step > end:
                return
            background = backgrounds.process_background_nearest(image)
            contain = contains.find_contain(background.uid)
            particles = self.process_particle_image(
                background, contain, image, step, ext_json
            )
            for particle in particles:
                cv2.ellipse(
                    image,
                    (particle.center, particle.radius, particle.angle),
                    (0, 255, 0),
                    2,
                )
            if debug:
                cv2.imshow(f"{self.config.video_name}", image)
                cv2.waitKey(delay=10)
            out.write(image)

        process_wrap(fun, self.config, desc="save video")
        out.release()

    @property
    def particle_df(self):
        return pd.DataFrame([par.to_json() for par in self.particle_list])

    def _save(self, *args, **kwargs):
        with open(self.filepath, "wb") as fw:
            pickle.dump(self.particle_list, fw)
        self.particle_df.to_csv(self.particle_csv_path, index=False)

    def _read(self, *args, **kwargs):
        with open(self.filepath, "rb") as fr:
            self.particle_list = pickle.load(fr)
        return True
