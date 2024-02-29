"""VTEC event metadata"""

import datetime
import json

from pyiem.reference import ISO8601
from pyiem.util import get_dbconnc, html_escape
from pyiem.webutil import iemapp
from pymemcache.client import Client


def run(wfo, year, phenomena, significance, etn):
    """Do great things"""
    pgconn, cursor = get_dbconnc("postgis")

    # This is really a BUG here and we need to rearch the database
    cursor.execute(
        f"""
    SELECT
    first_value(report) OVER (ORDER by product_issue ASC) as report,
    first_value(svs) OVER (ORDER by length(svs) DESC NULLS LAST
        ) as svs_updates,
    first_value(issue at time zone 'UTC')
        OVER (ORDER by issue ASC NULLS LAST) as utc_issue,
    first_value(expire at time zone 'UTC')
        OVER (ORDER by expire DESC NULLS LAST) as utc_expire
    from warnings_{year} w
    WHERE w.wfo = %s and eventid = %s and
    phenomena = %s and significance = %s
    """,
        (wfo, etn, phenomena, significance),
    )
    res = {
        "generation_time": datetime.datetime.utcnow().strftime(ISO8601),
        "year": year,
        "phenomena": phenomena,
        "significance": significance,
        "etn": etn,
        "wfo": wfo,
    }
    if cursor.rowcount == 0:
        pgconn.close()
        return json.dumps(res)

    row = cursor.fetchone()
    res["report"] = {"text": row["report"]}
    res["svs"] = []
    if row["svs_updates"] is not None:
        for token in row["svs_updates"].split("__"):
            if token.strip() != "":
                res["svs"].append({"text": token})
    res["utc_issue"] = row["utc_issue"].strftime(ISO8601)
    res["utc_expire"] = row["utc_expire"].strftime(ISO8601)

    # Now lets get UGC information
    cursor.execute(
        f"""
    SELECT
    u.ugc,
    u.name,
    w.status,
    w.product_issue at time zone 'UTC' utc_product_issue,
    w.issue at time zone 'UTC' utc_issue,
    w.expire at time zone 'UTC' utc_expire,
    w.init_expire at time zone 'UTC' utc_init_expire,
    w.updated at time zone 'UTC' utc_updated, hvtec_nwsli
    from warnings_{year} w JOIN ugcs u on (w.gid = u.gid)
    WHERE w.wfo = %s and eventid = %s and
    phenomena = %s and significance = %s
    ORDER by u.ugc ASC
    """,
        (wfo, etn, phenomena, significance),
    )
    res["ugcs"] = []
    for row in cursor:
        res["ugcs"].append(
            {
                "ugc": row["ugc"],
                "name": row["name"],
                "status": row["status"],
                "hvtec_nwsli": row["hvtec_nwsli"],
                "utc_product_issue": row["utc_product_issue"].strftime(
                    ISO8601
                ),
                "utc_issue": row["utc_issue"].strftime(ISO8601),
                "utc_init_expire": row["utc_init_expire"].strftime(ISO8601),
                "utc_expire": row["utc_expire"].strftime(ISO8601),
                "utc_updated": row["utc_updated"].strftime(ISO8601),
            }
        )
    pgconn.close()
    return json.dumps(res)


@iemapp()
def application(environ, start_response):
    """Answer request."""
    wfo = environ.get("wfo", "MPX")
    if len(wfo) == 4:
        wfo = wfo[1:]
    try:
        year = int(environ.get("year", 2015))
    except ValueError:
        year = 0
    if year < 1986 or year > datetime.date.today().year + 1:
        headers = [("Content-type", "text/plain")]
        start_response("500 Internal Server Error", headers)
        data = "Invalid Year"
        return [data.encode("ascii")]

    phenomena = environ.get("phenomena", "SV")[:2]
    significance = environ.get("significance", "W")[:1]
    try:
        etn = int(environ.get("etn", 1))
    except ValueError:
        headers = [("Content-type", "text/plain")]
        start_response("500 Internal Server Error", headers)
        data = "Invalid ETN"
        return [data.encode("ascii")]
    cb = environ.get("callback", None)

    mckey = f"/json/vtec_event/{wfo}/{year}/{phenomena}/{significance}/{etn}"
    mc = Client("iem-memcached:11211")
    res = mc.get(mckey)
    if not res:
        res = run(wfo, year, phenomena, significance, etn)
        mc.set(mckey, res, 300)
    else:
        res = res.decode("utf-8")
    mc.close()

    if cb is not None:
        res = f"{html_escape(cb)}({res})"

    headers = [("Content-type", "application/json")]
    start_response("200 OK", headers)
    return [res.encode("utf-8")]
