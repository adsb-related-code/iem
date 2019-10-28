"""Generate a map of today's record high and low temperature"""

import datetime

from pyiem.plot import MapPlot
from pyiem.network import Table as NetworkTable
from pyiem.util import get_dbconn


def main():
    """Go Main Go"""
    now = datetime.datetime.now()
    nt = NetworkTable("IACLIMATE")
    nt.sts["IA0200"]["lon"] = -93.6
    nt.sts["IA5992"]["lat"] = 41.65
    coop = get_dbconn("coop", user="nobody")

    # Compute normal from the climate database
    sql = """
        SELECT station, max_high, min_low from climate WHERE valid = '2000-%s'
        and substr(station,0,3) = 'IA'
    """ % (
        now.strftime("%m-%d"),
    )

    obs = []
    cursor = coop.cursor()
    cursor.execute(sql)
    for row in cursor:
        sid = row[0]
        if sid[2] == "C" or sid[2:] == "0000" or sid not in nt.sts:
            continue
        obs.append(
            dict(
                id=sid[2:],
                lat=nt.sts[sid]["lat"],
                lon=nt.sts[sid]["lon"],
                tmpf=row[1],
                dwpf=row[2],
            )
        )

    mp = MapPlot(
        title=("Record High + Low Temperature [F] (1893-%s)") % (now.year,),
        subtitle="For Date: %s" % (now.strftime("%d %b"),),
        continentalcolor="white",
    )
    mp.drawcounties()
    mp.plot_station(obs)
    pqstr = (
        "plot ac %s0000 climate/iowa_today_rec_hilo_pt.png "
        "coop_rec_temp.png png"
    ) % (now.strftime("%Y%m%d"),)
    mp.postprocess(view=False, pqstr=pqstr)
    mp.close()


if __name__ == "__main__":
    main()
