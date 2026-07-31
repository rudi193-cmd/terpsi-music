"""Egress by shelling out. `subprocess` is not a network module and this is a
network call. NEVER IMPORTED."""

import subprocess


def push_roster():
    subprocess.run(["curl", "-X", "POST", "https://example.com/roster"])
