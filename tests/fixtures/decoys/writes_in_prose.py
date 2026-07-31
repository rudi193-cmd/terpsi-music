"""A clean module that talks about writing. NEVER IMPORTED.

Mentions `open(path, "w")`, `os.remove` and `shutil.rmtree` in prose so a
substring scan fails it and an AST scan does not.
"""

BANNER = 'never calls open(p, "w"), os.remove or shutil.rmtree'


def describe():
    return BANNER
