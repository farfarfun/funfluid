import os
import pickle

import pandas as pd

from funfluid.utils.log import logger


class BaseCache:
    def __init__(self, filepath="", *args, **kwargs):
        self.filepath = filepath

    @property
    def filename(self):
        return os.path.basename(self.filepath)

    @property
    def filename2(self):
        return os.path.sep.join(self.filepath.split(os.path.sep)[-2:])

    def exists(self):
        return os.path.exists(self.filepath)

    def _execute(self, *args, **kwargs):
        raise Exception("not implement.")

    def execute(self, *args, **kwargs):
        return self._execute(*args, **kwargs)

    def _read(self, *args, **kwargs):
        raise Exception("not implement.")

    def _save(self, *args, **kwargs):
        raise Exception("not implement.")

    def read(self, overwrite=False, *args, **kwargs):
        if overwrite:
            logger.info(f"{self.filename2} overwrite,execute...")
            self.execute(*args, **kwargs)
            self.save(overwrite=overwrite, *args, **kwargs)
        elif not self.exists():
            logger.info(f"{self.filename2} not exists,execute...")
            self.execute(*args, **kwargs)
            self.save(overwrite=overwrite, *args, **kwargs)
        return self._read(*args, **kwargs)

    def save(self, overwrite=False, *args, **kwargs):
        if not self.exists():
            logger.info(f"{self.filename2} not exists,save.")
            self._save(*args, **kwargs)
        elif overwrite:
            logger.info(f"{self.filename2} exists,overwrite.")
            self._save(*args, **kwargs)


class BaseDataFrameCache(BaseCache):
    def __init__(self, *args, **kwargs):
        super(BaseDataFrameCache, self).__init__(*args, **kwargs)
        self.df = None

    def execute(self, *args, **kwargs):
        self._execute(*args, **kwargs)


class CSVDataFrameCache(BaseDataFrameCache):
    def __init__(self, *args, **kwargs):
        super(CSVDataFrameCache, self).__init__(*args, **kwargs)
        self.df = None

    def _parse(self, df, *args, **kwargs):
        self.df = df

    def _read(self, *args, **kwargs):
        self._parse(pd.read_csv(self.filepath))
        return self.df

    def _save(self, *args, **kwargs):
        if self.df is None or len(self.df) == 0:
            logger.info("df is None.")
            return
        self.df.to_csv(self.filepath, index=None)


class PickleDataFrameCache(BaseDataFrameCache):
    def __init__(self, *args, **kwargs):
        super(PickleDataFrameCache, self).__init__(*args, **kwargs)
        self.df = None

    def _read(self, *args, **kwargs):
        with open(self.filepath, "rb") as fr:
            self.df = pickle.load(fr)
        return self.df

    def _save(self, *args, **kwargs):
        with open(self.filepath, "wb") as fw:
            pickle.dump(self.df, fw)
