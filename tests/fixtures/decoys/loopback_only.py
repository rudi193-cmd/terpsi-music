"""A listener that stays on the loopback, which a manifest can honestly declare.

NEVER IMPORTED.
"""

import socket


def local_console():
    sock = socket.socket()
    sock.bind(("127.0.0.1", 8560))
    sock.listen(1)
    return sock
