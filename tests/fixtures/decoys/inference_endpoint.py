"""A provider reached with no router and no SDK. NEVER IMPORTED.

The hole a router-shaped checker leaves: forty lines of `urllib` and a bearer
token reach Groq without importing anything the fleet watches, and a
`subprocess` call to `curl` does it without importing anything at all. Both are
`inference_router._openai_chat` rewritten by somebody in a hurry.

The third function is the quieter one: a request straight to the **local**
runner. It is on the right machine and it is still a finding, because it
returns no provider label — there is nothing for `records.inference.accept` to
check, and the shape refusal 1 is enforced by is gone.

`tools/providers.py` must report all three.
"""

import json
import subprocess
import urllib.request

KEY = "unset"


def ask_groq(system, user):
    body = json.dumps({"messages": [{"role": "user", "content": user}]}).encode()
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=body,
        headers={"Authorization": f"Bearer {KEY}"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)["choices"][0]["message"]["content"]


def ask_via_shell(user):
    return subprocess.run(
        ["curl", "-s", "https://generativelanguage.googleapis.com/v1beta/models"],
        capture_output=True, text=True,
    ).stdout


def ask_local(user):
    body = json.dumps({"model": "llama3.2:3b", "prompt": user}).encode()
    req = urllib.request.Request("http://localhost:11434/api/generate", data=body)
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.load(r)["response"]
