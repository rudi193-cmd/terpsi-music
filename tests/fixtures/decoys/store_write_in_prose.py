"""A module that only talks about writing to the store, and must not be flagged.

The counterpart decoy, against the wrong implementation. A grep for `INSERT
INTO` fails this file; `tools/purity.py` must not, because a rule written in
prose is not the rule being broken — the same false positive `tools/discipline.py`
recorded against its own decoy, and the reason a check that cries wolf gets
switched off.
"""

RULE = "never run INSERT INTO lane_entry outside the declared write path"


def explain():
    """Say what is forbidden. This function executes nothing.

    UPDATE, DELETE FROM and TRUNCATE are all forbidden to the app role too, and
    naming them here is documentation rather than a write.
    """
    return RULE
