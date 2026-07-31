"""Filesystem writes of every shape the core forbids. NEVER IMPORTED."""

import os
import shutil
from pathlib import Path


def persist(payload):
    with open("/var/lib/terpsi/roster.json", "w") as fh:
        fh.write(payload)
    Path("/var/lib/terpsi/notes.txt").write_text(payload)
    Path("/var/lib/terpsi/blob").write_bytes(b"x")
    os.makedirs("/var/lib/terpsi/season", exist_ok=True)
    os.remove("/var/lib/terpsi/old.json")
    shutil.rmtree("/var/lib/terpsi/last-season")
