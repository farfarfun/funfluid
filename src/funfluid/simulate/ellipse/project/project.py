import math
import os

import pandas as pd


class BaseProject:
    def __init__(self, path):
        self.path = path

    @staticmethod
    def _load(path, index=0, type=1):
        df = pd.read_csv(path, sep="\s+", header=None)
        cols = [f"c{i}" for i in df.columns]
        cols[0] = "x"
        cols[1] = "y"
        cols[4] = "theta"
        cols[11] = "step"
        df.columns = cols
        if type == 1:
            df["theta"] = (df["theta"]) * math.pi / 180.0
        else:
            df["theta"] = (df["theta"]) * math.pi
        # df = df.reset_index(names='step')
        df["step"] = df["step"].astype("int")
        df["index"] = index
        return df

    @property
    def orientation_files(self):
        results = []
        for file in os.listdir(self.path):
            if file.startswith("orientation"):
                results.append(os.path.join(self.path, file))
        results.sort(key=lambda x: x)
        return results

    def output_path(self, sub_path=""):
        path = os.path.join(self.path, "output", sub_path)
        if not os.path.exists(path):
            os.makedirs(path)
        return path

    @property
    def project_name(self):
        return os.path.basename(self.path)
