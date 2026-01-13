import json
import logging
import os

from funfluid.experiment.chlamydomonas.base.globalconfig import GlobalConfig
from funfluid.experiment.chlamydomonas.progress.video_progress import VideoProgress
from funfluid.utils.log import logger

logger.setLevel(logging.INFO)


class MainProgress:
    def __init__(self, config: GlobalConfig):
        self.config = config

    def run(self, debug=False):
        result = []
        for root, directories, files in os.walk(self.config.videos_dir):
            if root.endswith("useless"):
                continue

            for file in files:
                if not file.endswith(".avi") and not file.endswith(".mp4"):
                    continue
                ext_json = {"file": file}

                video_split = self.config.get_result_path(
                    video_path=os.path.join(root, file)
                )
                if video_split is None:
                    continue
                video_progress = VideoProgress(video_split=video_split)
                result.append(video_progress.execute(ext_json=ext_json, debug=debug))

        with open(self.config.results_json, "w") as fr:
            fr.write(json.dumps(result))
        logger.info("all is done")
