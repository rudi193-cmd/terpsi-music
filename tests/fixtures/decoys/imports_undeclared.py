"""A decoy for tools/imports.py: a third-party import that requirements.txt does
not declare. It must be a FINDING. Never run, never imported by the app — it
lives here so the stdlib-only gate is shown to fire (rule 19), the way
driver_*.py does for tools/drivers.py."""
import requests          # noqa — the forbidden act: an undeclared dependency
from flask import Flask  # noqa — and a second, by the from-form

__all__ = ["requests", "Flask"]
