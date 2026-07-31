"""A module outside `store/` that imports the database driver.

The decoy for `tools/drivers.py`. The dependency was accepted narrowly — the
store may talk to PostgreSQL and nothing else may — and a module holding this
import can connect on any line written after it, with no adapter narrating the
read, no role restricting the write and no write-path declaration covering
either.
"""

import psycopg


def sneak(dsn):
    return psycopg.connect(dsn)
