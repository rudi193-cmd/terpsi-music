"""A network import one directory down. NEVER IMPORTED.

The original checker globbed `*.py` rather than `**/*.py`, so a subpackage was
invisible to it and reported as clean.
"""

import socket

CONN = socket.create_connection
