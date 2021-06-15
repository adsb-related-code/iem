"""Dump NASS Quickstats to the IEM database.

Run from RUN_10_AFTER.sh at 3 PM each day."""
import sys
from datetime import datetime, timedelta

import requests
import pytz
import numpy as np
import pandas as pd
from pyiem.util import get_dbconn, logger, get_properties

LOG = logger()
TMP = "/mesonet/tmp"
PROPS = get_properties()
TOPICS = [
    {"commodity_desc": "CORN"},
    {"commodity_desc": "SOYBEANS"},
    {"commodity_desc": "SOIL", "statisticcat_desc": "MOISTURE"},
]
SERVICE = "https://quickstats.nass.usda.gov/api/api_GET/"


def get_df(year, sts, topic):
    """Figure out the data we need."""
    params = {
        "key": PROPS["usda.quickstats.key"],
        "format": "JSON",
        "program_desc": "SURVEY",
        "sector_desc": "CROPS",
        "agg_level_desc": "STATE",
        "freq_desc": "WEEKLY",
    }
    if year is not None:
        params["year"] = year
    if sts is not None:
        params["load_time__GE"] = sts.strftime("%Y-%m-%d %H:%M:%S")
    params.update(topic)
    req = requests.get(SERVICE, params, timeout=300)
    if req.status_code != 200:
        LOG.info("Got status_code %s %s", req.status_code, req.url)
        return
    data = req.json()
    return pd.DataFrame(data["data"])


def process(df):
    """Do some work"""
    # Try to get a number
    df["num_value"] = pd.to_numeric(df["Value"], errors="coerce")
    for col in ["asd_code", "county_ansi", "zip_5"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    # Get load_time in proper order
    df["load_time"] = pd.to_datetime(
        df["load_time"], format="%Y-%m-%d %H:%M:%S"
    ).dt.tz_localize(pytz.timezone("America/New_York"))
    df = df.replace({np.nan: None})
    pgconn = get_dbconn("coop")
    cursor = pgconn.cursor()
    deleted = 0
    inserted = 0
    dups = 0
    for _, row in df.iterrows():
        # Uniqueness by short_desc, year, state_alpha, week_ending
        cursor.execute(
            "SELECT load_time from nass_quickstats where year = %s "
            "and short_desc = %s and state_alpha = %s and week_ending = %s",
            (
                row["year"],
                row["short_desc"],
                row["state_alpha"],
                row["week_ending"],
            ),
        )
        if cursor.rowcount > 0:
            lt = cursor.fetchone()[0]
            if lt == row["load_time"].to_pydatetime():
                dups += 1
                continue
            cursor.execute(
                "DELETE from nass_quickstats where year = %s "
                "and short_desc = %s and "
                "state_alpha = %s and week_ending = %s",
                (
                    row["year"],
                    row["short_desc"],
                    row["state_alpha"],
                    row["week_ending"],
                ),
            )
            deleted += cursor.rowcount
        inserted += 1
        cursor.execute(
            """
            INSERT into nass_quickstats(
            short_desc,
            source_desc, sector_desc,
            group_desc,
            commodity_desc,
            class_desc,
            prodn_practice_desc,
            util_practice_desc,
            statisticcat_desc,
            unit_desc,
            agg_level_desc,
            state_alpha,
            asd_code,
            county_ansi,
            country_code,
            year,
            freq_desc,
            begin_code,
            end_code,
            week_ending,
            load_time,
            value,
            cv,
            num_value) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                row["short_desc"],
                row["source_desc"],
                row["sector_desc"],
                row["group_desc"],
                row["commodity_desc"],
                row["class_desc"],
                row["prodn_practice_desc"],
                row["util_practice_desc"],
                row["statisticcat_desc"],
                row["unit_desc"],
                row["agg_level_desc"],
                row["state_alpha"],
                row["asd_code"],
                row["county_ansi"],
                row["country_code"],
                row["year"],
                row["freq_desc"],
                row["begin_code"],
                row["end_code"],
                row["week_ending"],
                row["load_time"],
                row["Value"],
                row["CV (%)"],
                row["num_value"],
            ),
        )
    cursor.close()
    pgconn.commit()
    LOG.info("Deleted %s, Inserted %s, Dups %s rows", deleted, inserted, dups)


def main(argv):
    """Go Main Go"""
    # Figure out a load_time
    if len(argv) == 2:
        LOG.info("Re-running all!")
        sts = None
        years = range(1980, datetime.now().year + 1)
    else:
        years = [None]
        sts = (datetime.now() - timedelta(days=1)).replace(
            hour=0, minute=0, second=0
        )

    for year in years:
        for topic in TOPICS:
            df = get_df(year, sts, topic)
            if df is not None:
                process(df)


if __name__ == "__main__":
    main(sys.argv)
