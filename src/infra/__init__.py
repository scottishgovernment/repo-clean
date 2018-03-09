from datetime import date, timedelta

EARLIEST_RELEASE_DATE = date.today() - timedelta(days=90)
STALE_DATE = EARLIEST_RELEASE_DATE - timedelta(days=1)

# eof
