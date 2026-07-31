"""Every spelling of revocation-by-delete. NEVER IMPORTED.

The shipped regex matched none of these and flagged a clean file instead.
"""

def revoke(edges, eid, store):
    del edges[0]
    self._edges.remove(eid)
    store.execute("DELETE FROM edge WHERE edge_id = ?", (eid,))
    grants.clear()
    guardians.discard(eid)
