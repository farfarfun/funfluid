import pandas as pd


def read_tecplot_point(path):
    data = open(path, "r").read().split("\n")
    cols = [col for col in data[0].split("=")[1].strip().split(",")]
    zone = dict(
        [
            (kv.split("=")[0].strip(), kv.split("=")[1].strip())
            for kv in data[1].strip("ZONE").strip().split(",")
        ]
    )
    df = pd.read_csv(path, header=None, sep="\s+", nrows=int(zone["N"]), skiprows=2)
    df.columns = cols
    return df
