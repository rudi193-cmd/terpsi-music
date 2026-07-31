"""A clean module that talks about egress. NEVER IMPORTED.

Says `import socket`, `from urllib.request import urlopen` and
`subprocess.run(["curl"])` in prose so a grep-based checker fails it and an
AST-based one does not.
"""

import hashlib

NOTE = "does not import socket, never calls urllib.request or subprocess"


def digest(x):
    return hashlib.sha256(x.encode()).hexdigest()
