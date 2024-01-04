"""Clean up some tables that contain bloaty NWS Text Data

called from RUN_2AM.sh
"""

from pyiem.reference import state_names
from pyiem.util import get_dbconn, logger

LOG = logger()


def main():
    """Clean AFOS and friends"""
    pgconn = get_dbconn("afos")
    acursor = pgconn.cursor()

    # reflect changes to docs/datasets/afos.md
    # RRM removed due to request
    pil3 = (
        "^(RR[1-9RSAZ]|ECM|ECS|ECX|LAV|LEV|MAV|MET|MTR|MEX|NBE|NBH|NBP|NBS|"
        "NBX|OSO|RSD|RWR|STO|HML|WRK|SCV|LLL)"
    )
    pils = (
        "HPTNCF WTSNCF TSTNCF HD3RSA XF03DY XOBUS ECMNC1 SYNBOU MISWTM MISWTX "
        "MISMA1 MISAM1"
    ).split()
    for abbr in state_names:
        # SCNWSH, le sigh
        pils.append(f"SCN{abbr}")
    acursor.execute(
        """
        delete from products WHERE
        entered < ('YESTERDAY'::date - '7 days'::interval) and
        entered > ('YESTERDAY'::date - '31 days'::interval) and
        (pil ~* %s or pil = ANY(%s))
        """,
        (pil3, pils),
    )
    if acursor.rowcount == 0:
        LOG.warning("Found no products to delete between 7-31 days")
    acursor.close()
    pgconn.commit()


if __name__ == "__main__":
    main()
