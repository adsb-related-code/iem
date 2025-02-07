""".. title:: Request Hour's worth of METARs

Documentation for /cgi-bin/request/metars.py
--------------------------------------------

This is a very simple service that intends on emitting a text file of METARs
that is ammenable to being ingested by other software.  Each METAR is on a
single line and the file is sorted by the observation time.

Example Usage:
--------------

Retrieve all METARs for the hour starting at 00 UTC on 1 January 2016:

    https://mesonet.agron.iastate.edu/cgi-bin/request/metars.py?valid=2016010100

CGI Parameters:
---------------

* `valid`: The hour over which to return data.  The format is `YYYYMMDDHH` and
    would include any observations between that time and the next hour.

"""

import datetime
import sys
from io import StringIO
from zoneinfo import ZoneInfo

from pyiem.webutil import iemapp


def check_load(cursor):
    """A crude check that aborts this script if there is too much
    demand at the moment"""
    cursor.execute(
        "select pid from pg_stat_activity where query ~* 'FETCH' "
        "and datname = 'asos'"
    )
    if len(cursor.fetchall()) > 9:
        sys.stderr.write(
            f"/cgi-bin/request/metars.py over capacity: {cursor.rowcount}\n"
        )
        return False
    return True


@iemapp(iemdb="asos", iemdb_cursorname="streamer", help=__doc__)
def application(environ, start_response):
    """Do Something"""
    cursor = environ["iemdb.asos.cursor"]
    if not check_load(cursor):
        start_response(
            "503 Service Unavailable", [("Content-type", "text/plain")]
        )
        return [b"ERROR: server over capacity, please try later"]
    start_response("200 OK", [("Content-type", "text/plain")])
    valid = datetime.datetime.strptime(
        environ.get("valid", "2016010100")[:10], "%Y%m%d%H"
    )
    valid = valid.replace(tzinfo=ZoneInfo("UTC"))
    cursor.execute(
        """
        SELECT metar from alldata
        WHERE valid >= %s and valid < %s and metar is not null
        ORDER by valid ASC
    """,
        (valid, valid + datetime.timedelta(hours=1)),
    )
    sio = StringIO()
    for row in cursor:
        sio.write("%s\n" % (row["metar"].replace("\n", " "),))
    return [sio.getvalue().encode("ascii", "ignore")]
