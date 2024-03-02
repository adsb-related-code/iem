"""Generate a GeoJSON of current storm based warnings"""

import datetime
import json

from pyiem.reference import ISO8601
from pyiem.util import get_dbconnc, html_escape
from pyiem.webutil import iemapp
from pymemcache.client import Client


def run():
    """Actually do the hard work of getting the current SBW in geojson"""
    pgconn, cursor = get_dbconnc("mesosite")

    utcnow = datetime.datetime.utcnow()

    cursor.execute(
        "SELECT ST_asGeoJson(extent) as geojson, id, name "
        "from networks WHERE extent is not null ORDER by id ASC"
    )

    res = {
        "type": "FeatureCollection",
        "features": [],
        "generation_time": utcnow.strftime(ISO8601),
        "count": cursor.rowcount,
    }
    for row in cursor:
        res["features"].append(
            dict(
                type="Feature",
                id=row["id"],
                properties=dict(name=row["name"]),
                geometry=json.loads(row["geojson"]),
            )
        )
    pgconn.close()
    return json.dumps(res)


@iemapp()
def application(environ, start_response):
    """Do Something"""
    # Go Main Go
    headers = [("Content-type", "application/vnd.geo+json")]

    cb = environ.get("callback", None)

    mckey = "/geojson/network.geojson"
    mc = Client("iem-memcached:11211")
    res = mc.get(mckey)
    if not res:
        res = run()
        mc.set(mckey, res, 86400)
    else:
        res = res.decode("utf-8")
    mc.close()
    if cb is not None:
        res = f"{html_escape(cb)}({res})"

    start_response("200 OK", headers)
    return [res.encode("ascii")]
