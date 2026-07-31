"""A clean module that talks about deleting. NEVER IMPORTED.

Says `edges.remove(`, `del edges[0]` and `DELETE FROM edge` in prose so a
regex-over-lines checker fails it and an AST scan does not. This exact file
shape is what the shipped check flagged while missing five real deletions.
"""

NOTE = "revocation sets invalid_at; never edges.remove( ) and never DELETE FROM edge"
