import logging

from funfluid.experiment.chlamydomonas.analyse.analyse import TrackAnalyse, MSDCalculate
from funfluid.experiment.chlamydomonas.base.base import VideoBase
from funfluid.experiment.chlamydomonas.base.globalconfig import VideoSplit
from funfluid.experiment.chlamydomonas.detect.background import BackGroundDetect
from funfluid.experiment.chlamydomonas.detect.contain import ContainDetect
from funfluid.experiment.chlamydomonas.detect.particle import ParticleDetect
from funfluid.utils.log import logger

logger.setLevel(logging.INFO)


class VideoProgress:
    def __init__(self, video_split: VideoSplit):
        self.video_split = video_split
        self.base_video = VideoBase(video_split)
        self.detect_background = BackGroundDetect(config=self.base_video)
        self.detect_particle = ParticleDetect(config=self.base_video)
        self.detect_contain = ContainDetect(config=self.base_video)

        self.analyse_track = TrackAnalyse(config=self.base_video)
        self.analyse_msd = MSDCalculate(config=self.base_video)

    def execute(self, ext_json=None, debug=False):
        ext_json = ext_json or {}

        try:
            self.base_video.read()
            self.detect_background.read()
            self.detect_contain.read(backgrounds=self.detect_background, debug=debug)
            self.detect_particle.read(
                backgrounds=self.detect_background,
                contains=self.detect_contain,
                debug=debug,
            )

            # self.detect_particle.save_image(backgrounds=self.detect_background, contains=self.detect_contain,
            #                                 start=6337, end=6389,
            #                                 debug=debug)
            # self.detect_particle.save_gif(backgrounds=self.detect_background, contains=self.detect_contain,
            #                              start=6377, end=6389, debug=debug)
            # self.detect_particle.save_video(backgrounds=self.detect_background, contains=self.detect_contain,
            #                                start=6300, end=6550, debug=debug)

            self.analyse_track.read(
                contains=self.detect_contain, particles=self.detect_particle
            )
            self.analyse_msd.read(
                track=self.analyse_track, contains=self.detect_contain
            )
            ext_json.update(self.video_split.to_json())
            ext_json.update(self.base_video.to_json())
            ext_json.update(
                {
                    "particles": len(self.detect_particle.particle_list),
                    "tracks": len(self.analyse_track.df),
                    "background_size": len(self.detect_background.background_list),
                    "backcontain_size": len(self.detect_contain.contain_list),
                    "track_path": self.analyse_track.filepath,
                    "msd_path": self.analyse_msd.filepath,
                }
            )
        except Exception as e:
            print(f"main_error {self.base_video.video_paths[0]}")
        return ext_json
