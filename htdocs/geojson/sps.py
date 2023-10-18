""" Generate a GeoJSON of current SPS Polygons """
import datetime
import json

from pyiem.util import get_dbconnc, html_escape
from pyiem.webutil import iemapp
from pymemcache.client import Client


def run():
    """Actually do the hard work of getting the current SPS in geojson"""
    pgconn, cursor = get_dbconnc("postgis")

    utcnow = datetime.datetime.utcnow()

    # Look for polygons into the future as well as we now have Flood products
    # with a start time in the future
    cursor.execute(
        """
        SELECT ST_asGeoJson(geom) as geojson, product_id,
        issue at time zone 'UTC' as utc_issue,
        expire at time zone 'UTC' as utc_expire
        from sps WHERE issue < now() and expire > now()
        and not ST_IsEmpty(geom) and geom is not null
    """
    )

    res = {
        "type": "FeatureCollection",
        "features": [],
        "generation_time": utcnow.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "count": cursor.rowcount,
    }
    for row in cursor:
        sts = row["utc_issue"].strftime("%Y-%m-%dT%H:%M:%SZ")
        ets = row["utc_expire"].strftime("%Y-%m-%dT%H:%M:%SZ")
        href = f"/api/1/nwstext/{row['product_id']}"
        res["features"].append(
            dict(
                type="Feature",
                id=row["product_id"],
                properties=dict(href=href, issue=sts, expire=ets),
                geometry=json.loads(row["geojson"]),
            )
        )
    pgconn.close()
    return json.dumps(res)


@iemapp()
def application(environ, start_response):
    """Do Main"""
    headers = [("Content-type", "application/vnd.geo+json")]

    cb = environ.get("callback", None)

    mckey = "/geojson/sps.geojson"
    mc = Client("iem-memcached:11211")
    res = mc.get(mckey)
    if not res:
        res = run()
        mc.set(mckey, res, 15)
    else:
        res = res.decode("utf-8")
    mc.close()

    if cb is not None:
        res = f"{html_escape(cb)}({res})"

    start_response("200 OK", headers)
    return [res.encode("ascii")]
