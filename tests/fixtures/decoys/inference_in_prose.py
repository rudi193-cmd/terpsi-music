"""A clean module that talks about inference. NEVER IMPORTED.

Says `from core.inference_router import respond`, names
`https://api.groq.com/openai/v1/chat/completions` and mentions
`http://localhost:11434/api/chat` in prose, so a grep-based checker fails it and
an AST-based one does not. Same argument as `egress_in_prose.py`: the decoy
that proves the checker is looking at code.

`tools/providers.py` must find nothing here.
"""

import hashlib

NOTE = (
    "does not import inference_router, never posts to api.groq.com, and holds "
    "no key for openrouter.ai or generativelanguage.googleapis.com"
)

ENDPOINTS_WE_DO_NOT_CALL = (
    "https://api.groq.com/openai/v1/chat/completions",
    "http://localhost:11434/api/chat",
)


def digest(x):
    return hashlib.sha256(x.encode()).hexdigest()
