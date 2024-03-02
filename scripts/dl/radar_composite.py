"""Write NEXRAD composite sector views to archive.

run from RUN_5MIN.sh
"""

import datetime
import os
import subprocess
import sys
import tempfile

import requests
from pyiem.util import exponential_backoff, get_dbconnc, logger, utc

LOG = logger()
N0QBASE = utc(2010, 11, 14)


def save(sectorName, file_name, dir_name, ts, routes, bbox=None):
    """Get an image and write it back to LDM for archiving"""
    tstamp = ts.strftime("%Y%m%d%H%M")
    nexrad = "nexrad" if ts < N0QBASE else "n0q"
    layers = (
        f"layers[]={nexrad}&layers[]=watch_by_county&layers[]=sbw&"
        "layers[]=uscounties"
    )
    if sectorName == "conus":
        layers = f"layers[]={nexrad}&layers[]=watch_by_county"
    uri = (
        f"http://iem.local/GIS/radmap.php?sector={sectorName}&"
        f"ts={tstamp}&{layers}"
    )
    if bbox is not None:
        uri = (
            f"http://iem.local/GIS/radmap.php?bbox={bbox}&ts={tstamp}&{layers}"
        )
    req = exponential_backoff(requests.get, uri, timeout=60)
    if req is None or req.status_code != 200:
        LOG.warning("%s failure", uri)
        return

    with tempfile.NamedTemporaryFile(delete=False) as tmpfd:
        tmpfd.write(req.content)

    cmd = [
        "pqinsert",
        "-p",
        f"plot {routes} {tstamp} {file_name} "
        f"{dir_name}/n0r_{tstamp[:8]}_{tstamp[8:]}.png png",
        tmpfd.name,
    ]
    subprocess.call(cmd)
    os.unlink(tmpfd.name)


def runtime(ts, routes):
    """Actually run for a time"""
    pgconn, pcursor = get_dbconnc("postgis")

    save("conus", "uscomp.png", "usrad", ts, routes)
    save("iem", "mwcomp.png", "comprad", ts, routes)
    for i in ["lot", "ict", "sd", "hun"]:
        save(i, f"{i}comp.png", f"{i}rad", ts, routes)

    # SEL starts in about 2007
    if ts.year < 2007:
        return

    # Now, we query for watches.
    pcursor.execute(
        """
        with data as (
            select sel, rank() OVER (PARTITION by sel ORDER by issued DESC),
            ST_xmax(geom), ST_xmin(geom), ST_ymax(geom), ST_ymin(geom)
            from watches where issued < %s and issued > %s)
        select trim(sel) as ss, st_xmax, st_xmin, st_ymax, st_ymin from data
        where rank = 1
        """,
        (ts, ts - datetime.timedelta(days=120)),
    )
    for row in pcursor:
        xmin = float(row["st_xmin"]) - 0.75
        ymin = float(row["st_ymin"]) - 0.75
        xmax = float(row["st_xmax"]) + 0.75
        ymax = float(row["st_ymax"]) + 1.5
        bbox = f"{xmin},{ymin},{xmax},{ymax}"
        sel = row["ss"].lower()
        save("custom", f"{sel}comp.png", f"{sel}rad", ts, routes, bbox)
    pgconn.close()


def main(argv):
    """Go Main Go"""
    ts = utc(*[int(x) for x in argv[1:6]])
    LOG.info("Running for %s", ts)
    # If we are near real-time, also check various archive points
    if (utc() - ts).total_seconds() > 1000:
        runtime(ts, "a")
        return
    runtime(ts, "ac")
    for hroff in [1, 3, 7, 12, 24]:
        valid = ts - datetime.timedelta(hours=hroff)
        uri = (
            f"http://iem.local/archive/data/{valid:%Y}/{valid:%m}/{valid:%d}/"
            f"comprad/n0r_{valid:%Y%m%d}_{valid:%H%M}.png"
        )
        req = requests.get(uri, timeout=15)
        if req.status_code == 404:
            LOG.warning("%s 404, rerunning %s", uri, valid)
            runtime(valid, "a")


if __name__ == "__main__":
    main(sys.argv)
