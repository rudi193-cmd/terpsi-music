"""A module that writes to the store from outside the declaration.

The decoy for gate G-C's write-path half. `manifest.json` declares `store/` and
three other paths; this file sits under none of them and hands an `INSERT` to a
cursor, which is the exact shape the acceptance list's last item names:
*"a write path appears that the manifest does not declare — the build fails
without anyone remembering to check."*

It is under `tests/fixtures/decoys/`, which `tools/manifest.py` excuses from the
ordinary scan, so it is reached only by the test that points the checker at it.
A decoy inside the scanned tree would make every run report the decoy.
"""


def stash(conn, lane_id, body):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO lane_entry (lane_id, kind, payload) VALUES (%s, %s, %s)",
            (lane_id, "note", body))
