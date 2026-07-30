"""grove/mcp_local.py:317's shape: a UDP socket to 8.8.8.8 for local-IP discovery.

Outbound, in the app's own namespace rather than the bridge's, so a declaration
scoped to the dashboard does not cover it. NEVER IMPORTED.
"""

import socket


def local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]
