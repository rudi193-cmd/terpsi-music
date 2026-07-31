"""Reads a file and writes nothing. NEVER IMPORTED.

A read is a filesystem dependency and is not a write; conflating them makes the
write check cry wolf until somebody switches it off.
"""


def load(path):
    with open(path) as fh:
        return fh.read()


def also_load(path):
    return open(path, "r").read()
