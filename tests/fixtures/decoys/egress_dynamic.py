"""Egress that no `import` statement declares. NEVER IMPORTED."""

import importlib


def sneak():
    mod = __import__("socket")
    other = importlib.import_module("urllib.request")
    return mod, other
