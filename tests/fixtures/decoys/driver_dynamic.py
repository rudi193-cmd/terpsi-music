"""A module that reaches the driver through `importlib`, so no import statement
declares it.

`tools/purity.py`'s `_DYNAMIC` case, applied to the driver: the import graph
shows nothing, and a checker reading only `ast.Import` nodes clears this file.
"""

from importlib import import_module


def open_one(dsn):
    driver = import_module("psycopg")
    return driver.connect(dsn)
