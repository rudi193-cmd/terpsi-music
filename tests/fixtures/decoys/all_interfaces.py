"""The willow-grove case: an all-interface listener in a "portless" app.

NEVER IMPORTED. Parsed by tools/sockets.py in tests/test_sockets.py.
"""

import socket
from http.server import HTTPServer, SimpleHTTPRequestHandler


def dashboard():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("0.0.0.0", 8560))
    sock.listen(5)
    return sock


def also_a_dashboard():
    return HTTPServer(("", 8561), SimpleHTTPRequestHandler)
