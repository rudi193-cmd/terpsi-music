"""A module that opens nothing, and says so in words a grep would trip over.

Mentions socket, bind, 0.0.0.0 and listen in prose so a text-matching checker
fails this file and an AST-based one does not. NEVER IMPORTED.
"""

import hashlib

BANNER = "this module does not bind 0.0.0.0 and opens no socket; it will not listen"


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()
