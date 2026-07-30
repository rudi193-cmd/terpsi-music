"""A bind whose address comes from config. Not resolvable, therefore not a pass.

NEVER IMPORTED.
"""

import os
import socket

HOST = os.environ.get("TERPSI_BIND", "0.0.0.0")
PORT = int(os.environ.get("TERPSI_PORT", "8560"))


def serve():
    sock = socket.socket()
    sock.bind((HOST, PORT))
    sock.listen(16)
    return sock
