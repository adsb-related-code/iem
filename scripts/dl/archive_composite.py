"""Regenerate composites to fulfill various reasons."""

import datetime
import subprocess
import sys

from pyiem.util import logger, utc

LOG = logger()


def main(argv):
    """Go Main Go"""
    sts = utc(*[int(x) for x in argv[1:6]])
    ets = utc(*[int(x) for x in argv[6:11]])
    interval = datetime.timedelta(minutes=5)
    now = sts
    while now < ets:
        cmd = f"python radar_composite.py {now:%Y %m %d %H %M}"
        LOG.info(cmd)
        subprocess.call(cmd.split())
        now += interval


if __name__ == "__main__":
    main(sys.argv)
