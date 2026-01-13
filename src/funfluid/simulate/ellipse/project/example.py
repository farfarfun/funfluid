from funfluid.simulate.ellipse.project.project import BaseProject
from funfluid.simulate.ellipse.project.track import EllipseTrack, FlowTrack, Canvas


class Project(BaseProject):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def analyse_track(self):
        track = FlowTrack()
        for index, file in enumerate(self.orientation_files):
            if index == 0:
                ellipse = EllipseTrack(
                    a=10, b=6, df=self._load(file, 0, type=1), color="r", line_width=1
                )
            elif index == 1:
                ellipse = EllipseTrack(
                    a=10, b=6, df=self._load(file, 0, type=1), color="b", line_width=1
                )
            else:
                continue

            track.add_ellipse(ellipse)

        # track.transform()

        # track.set_flow(Canvas(100, min(track.max_y, 1200) + 10, x_start=min(track.min_x - 10, 0)))
        track.set_canvas(
            Canvas(
                min(track.max_x, 120000) + 10,
                1000,
                x_start=min(track.min_x - 10, 0),
                y_start=15,
                aspect=2,
            )
        )
        # track.set_flow(Canvas(2000, 10, x_start=5000, y_start=15))

        track.plot(
            min_step=2,
            step=500,
            # min_step=80000, step=1500, max_step=130000,
            title=self.project_name + ",step={step}",
            gif_path=f"{self.output_path()}/{self.project_name}-track.gif",
        )
        # df = track.ellipses[0].df
        # plt.plot(df['x'], df['y'])
        # plt.pause(3000)


Project(f"/Users/bingtao/workspace/chen/flow0410/result/008").analyse_track()
