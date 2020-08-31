import datetime
from crontab import CronTab
import math
import warnings

warnings.simplefilter('ignore', FutureWarning)

class JobConfig(object):
    def __init__(self, crontab, job, delay=0):
        self._crontab = crontab
        self.job = job
        self.delay = delay

    def schedule(self):
        crontab = self._crontab
        return datetime.datetime.now() + datetime.timedelta(seconds=math.ceil(crontab.next()))

    def next(self):
        crontab = self._crontab
        return math.ceil(crontab.next()) + self.delay
