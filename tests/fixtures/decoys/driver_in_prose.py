"""A module that names the driver and never imports it.

`psycopg` appears four times in this file and `import psycopg` appears nowhere.
A grep fails this file; `tools/drivers.py` must not — the finding is an import,
not a word. `psycopg.connect` in a docstring is a sentence about psycopg.
"""

NOTE = "the store uses psycopg; nothing else may import psycopg"


def explain():
    return NOTE
