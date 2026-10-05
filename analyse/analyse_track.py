from funfluid.simulate.ellipse.project.project import BaseProject
from funfluid.simulate.ellipse.project.track import EllipseTrack, FlowBase, FlowTrack


class Project(BaseProject):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def analyse_track(self):
        track = FlowTrack()
        for index, file in enumerate(self.orientation_files):
            if index == 0:
                ellipse = EllipseTrack(a=10, b=10, df=self._load(file, 0), color="r")
            elif index == 1:
                ellipse = EllipseTrack(a=10, b=10, df=self._load(file, 0), color="b")
            else:
                continue

            ellipse.add_snapshot(step=100)
            ellipse.add_snapshot(step=4000)
            # ellipse.add_snapshot(step=1100)
            track.add_ellipse(ellipse)

            # track.transform()

        track.set_flow(FlowBase(1250, 100, x_start=1000))

        track.plot(
            # min_step=2, step=500,
            min_step=1000,
            step=50,
            # min_step=80000, step=1500, max_step=130000,
            # title=self.project_name + ',step={step}',
            title=r"$AR=0.2$",
            gif_path=f"{self.output_path()}/{self.project_name}-track.gif",
        )


Project("/Users/chen/workspace/chenflow/0606_doulbe/cmake-build-debug").analyse_track()
