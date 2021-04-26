"""Rectify climodat database entries."""
from io import StringIO
import sys

import pandas as pd
from pandas.io.sql import read_sql
from pyiem.network import Table as NetworkTable
from pyiem.util import get_dbconn, logger

LOG = logger()


def set_offline(iemid):
    """Set this station to offline stations."""
    pgconn = get_dbconn("mesosite")
    cursor = pgconn.cursor()
    cursor.execute(
        "UPDATE stations SET online = 'f' where iemid = %s",
        (iemid,),
    )
    cursor.close()
    pgconn.commit()


def main(argv):
    """Go Main"""
    state = argv[1]
    nt = NetworkTable(f"{state}CLIMATE", only_online=False)
    pgconn = get_dbconn("coop")
    df = read_sql(
        f"SELECT station, year, day from alldata_{state} "
        "ORDER by station, day",
        pgconn,
        index_col=None,
    )

    for station, gdf in df.groupby("station"):
        if station not in nt.sts:
            LOG.info(
                "station: %s is unknown to %sCLIMATE, skip", station, state
            )
            continue
        # Make sure that our data archive starts on the first of a month
        minday = gdf["day"].min().replace(day=1)
        missing = pd.date_range(minday, gdf["day"].max()).difference(
            gdf["day"]
        )
        if missing.empty:
            continue
        LOG.info(
            "station: %s [%s - %s], missing %s/%s days",
            station,
            gdf["day"].min(),
            gdf["day"].max(),
            len(missing),
            len(gdf.index),
        )
        missing_ratio = len(missing) / float(len(gdf.index))
        if (
            len(gdf.index) > 3000
            and missing_ratio > 0.33
            and nt.sts[station]["online"]
        ):
            LOG.info(
                "Online %s missing %.2f data, setting offline",
                station,
                missing_ratio,
            )
            set_offline(nt.sts[station]["iemid"])

        sio = StringIO()
        for day in missing:
            sio.write(
                ("%s,%s,%s,%s,%s\n")
                % (
                    station,
                    day,
                    "%02i%02i" % (day.month, day.day),
                    day.year,
                    day.month,
                )
            )
        sio.seek(0)
        cursor = pgconn.cursor()
        cursor.copy_from(
            sio,
            "alldata_%s" % (state,),
            columns=("station", "day", "sday", "year", "month"),
            sep=",",
        )
        del sio
        cursor.close()
        pgconn.commit()


if __name__ == "__main__":
    main(sys.argv)
