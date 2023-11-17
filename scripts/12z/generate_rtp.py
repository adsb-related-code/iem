"""
Generate a RTP product for the weather bureau.
"""
import datetime
import os
import subprocess
import tempfile

import pandas as pd
from pyiem.network import Table as NetworkTable
from pyiem.tracker import loadqc
from pyiem.util import get_sqlalchemy_conn, utc
from sqlalchemy import text

JOBS = [
    {
        "wfo": "DMX",
        "filename": "awos_rtp.shef",
        "networks": ["IA_ASOS", "ISUSM", "IA_DCP", "IA_RWIS"],
        "precip_works": ["IA_ASOS", "IL_ASOS", "ISUSM"],
        "limiter": "state = :state",
        "filter": ["state", "IA"],
        "state": "IA",
    },
    {
        "filename": "awos_rtp_dvn.shef",
        "networks": "IA_ASOS ISUSM IA_DCP IA_RWIS IL_RWIS IL_ASOS".split(),
        "precip_works": ["IA_ASOS", "IL_ASOS", "ISUSM"],
        "limiter": "wfo = :wfo",
        "filter": ["wfo", "DVN"],
        "wfo": "DVN",
    },
]


def main(job):
    """Go Main Go"""
    qdict = loadqc()

    # We run at 12z
    job["now12z"] = utc().replace(hour=12, minute=0, second=0, microsecond=0)
    job["today6z"] = job["now12z"].replace(hour=6)
    job["today0z"] = job["now12z"].replace(hour=0)
    job["yesterday6z"] = job["today6z"] - datetime.timedelta(days=1)
    job["yesterday12z"] = job["now12z"] - datetime.timedelta(days=1)

    asosfmt = "%-6s:%-43s: %3s / %3s / %5s\n"
    fmt = "%-6s:%-43s: %3s / %3s\n"

    job["badtemps"] = [sid for sid in qdict if qdict[sid].get("tmpf")]
    job["badprecip"] = [sid for sid in qdict if qdict[sid].get("precip")]
    with get_sqlalchemy_conn("iem") as conn:
        # 6z to 6z high temperature
        data = pd.read_sql(
            text(
                f"""
        SELECT id, round(max(tmpf)::numeric,0) as max_tmpf,
        count(tmpf) as obs FROM current_log c, stations t
        WHERE t.iemid = c.iemid and t.network = ANY(:networks) and
        valid >= :yesterday6z and valid < :today6z and {job['limiter']}
        and tmpf > -99 and not id = ANY(:badtemps) GROUP by id
                 """
            ),
            conn,
            params=job,
            index_col="id",
        )
        # 0z to 12z low temperature
        lows = pd.read_sql(
            text(
                f"""
        SELECT id, round(min(tmpf)::numeric,0) as min_tmpf,
        count(tmpf) as obs FROM
        current_log c JOIN stations t on (t.iemid = c.iemid)
        WHERE t.network = ANY(:networks) and valid >= :today0z
        and valid < :now12z and tmpf > -99 and not
        id = ANY(:badtemps) and {job['limiter']} GROUP by id
                """
            ),
            conn,
            params=job,
            index_col="id",
        )
        data["min_tmpf"] = lows["min_tmpf"]

        # 12z to 12z precip
        pcpn = pd.read_sql(
            text(
                f"""
        select id as station, sum(precip) from
        (select id, extract(hour from valid) as hour,
        max(phour) as precip from current_log c, stations t
        WHERE t.network = ANY(:networks) and t.iemid = c.iemid
        and valid >= :yesterday12z and valid < :now12z
        and not id = ANY(:badprecip) and {job['limiter']}
        GROUP by id, hour) as foo
        GROUP by id
    """
            ),
            conn,
            params=job,
            index_col="station",
        )
        pcpn = pcpn[pcpn["sum"].notna()]
        data["precip"] = pcpn["sum"]

    tt = job["yesterday6z"].strftime("%d %b %Y").upper()
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", delete=False
    ) as fh:
        fh.write("\n\n\n")
        for netid in job["networks"]:
            nt = NetworkTable(netid)
            ids = list(nt.sts.keys())
            ids.sort()
            for sid, meta in nt.sts.items():
                if meta[job["filter"][0]] != job["filter"][1]:
                    ids.remove(sid)
            if not ids:
                continue
            networkname = netid.replace("ASOS", "AWOS")
            precip_on = netid in job["precip_works"]
            fh.write(
                f".BR {job['wfo']} {job['now12z']:%m%d} Z "
                "DH06/TAIRVX/DH12/TAIRVP"
                f"{'/PPDRVZ' if precip_on else ''}\n"
                f": {networkname} RTP FIRST GUESS "
                "PROCESSED BY THE IEM\n"
                f":   06Z to 06Z HIGH TEMPERATURE FOR {tt}\n"
                ":   00Z TO 12Z TODAY LOW TEMPERATURE\n"
                ":   12Z YESTERDAY TO 12Z TODAY RAINFALL\n"
                ":   ...BASED ON REPORTED OBS...\n"
            )
            for sid in ids:
                if (
                    netid == "IA_ASOS"
                    and nt.sts[sid]["attributes"].get("IS_AWOS") != "1"
                ):
                    continue
                if netid == "IA_DCP" and nt.sts[sid]["name"].find("RAWS") < 0:
                    continue
                my_high = "M"
                my_low = "M"
                my_precip = "M"
                if sid in data.index:
                    row = data.loc[sid]
                    if not pd.isna(row["max_tmpf"]):
                        my_high = int(row["max_tmpf"].round(0))
                    if not pd.isna(row["min_tmpf"]):
                        my_low = int(row["min_tmpf"].round(0))
                    if not pd.isna(row["precip"]):
                        if 0 < row["precip"] < 0.009:
                            my_precip = "T"
                        else:
                            my_precip = f"{row['precip']:.02f}"
                _fmt = asosfmt if precip_on else fmt
                args = [
                    sid,
                    nt.sts[sid]["name"],
                    my_high,
                    my_low,
                    my_precip,
                ]
                if not precip_on:
                    args = args[:-1]
                fh.write(_fmt % tuple(args))

            fh.write(".END\n\n")

    pqstr = (
        f"plot ac {job['now12z']:%Y%m%d}0000 "
        f"{job['filename']} {job['filename']} shef"
    )
    subprocess.call(["pqinsert", "-p", pqstr, fh.name])
    os.unlink(fh.name)


if __name__ == "__main__":
    for _job in JOBS:
        main(_job)
