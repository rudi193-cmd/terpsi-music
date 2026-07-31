"""Revocation done correctly: a date, not a delete. NEVER IMPORTED."""

import dataclasses


def revoke(edge, at):
    return dataclasses.replace(edge, invalid_at=at)


def live(edges, at):
    """Deriving the live set. Character for character how you would drop a
    revoked row, which is why this scan does not flag comprehensions."""
    return [e for e in edges if e.live_at(at)]
