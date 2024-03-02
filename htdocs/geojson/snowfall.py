"""Produce geojson of Snowfall data"""

import datetime
import json

from pyiem.reference import TRACE_VALUE
from pyiem.util import html_escape
from pyiem.webutil import iemapp
from pymemcache.client import Client

json.encoder.FLOAT_REPR = lambda o: format(o, ".2f")


def sanitize(val):
    """convert to Ms"""
    if val is None:
        return "M"
    if val == TRACE_VALUE:
        return "T"
    return val


def get_data(cursor, ts):
    """Get the data for this timestamp"""
    data = {"type": "FeatureCollection", "features": []}
    # Fetch the daily values
    cursor.execute(
        """
    select id as station, name, state, wfo,
    round(st_x(geom)::numeric, 4)::float as st_x,
    round(st_y(geom)::numeric, 4)::float as st_y,
    snow
    from summary s JOIN stations t on (s.iemid = t.iemid)
    WHERE s.day = %s and s.snow >= 0 and t.network = 'IA_COOP' LIMIT 5
    """,
        (ts.date(),),
    )
    for i, row in enumerate(cursor):
        data["features"].append(
            {
                "type": "Feature",
                "id": i,
                "properties": {
                    "station": row["station"],
                    "state": row["state"],
                    "wfo": row["wfo"],
                    "name": row["name"],
                    "snow": str(sanitize(row["snow"])),
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [row["st_x"], row["st_y"]],
                },
            }
        )
    return json.dumps(data)


@iemapp(iemdb="iem", iemdb_cursorname="cursor")
def application(environ, start_response):
    """see how we are called"""
    dt = environ.get("dt", datetime.date.today().strftime("%Y-%m-%d"))
    ts = datetime.datetime.strptime(dt, "%Y-%m-%d")
    cb = environ.get("callback", None)
    headers = [("Content-type", "application/vnd.geo+json")]

    mckey = f"/geojson/snowfall/{ts:%Y%m%d}?callback={cb}"
    mc = Client("iem-memcached:11211")
    res = mc.get(mckey)
    if not res:
        res = get_data(environ["iemdb.iem.cursor"], ts)
        mc.set(mckey, res, 300)
    else:
        res = res.decode("utf-8")
    if cb is not None:
        res = f"{html_escape(cb)}({res})"

    start_response("200 OK", headers)
    return [res.encode("ascii")]
