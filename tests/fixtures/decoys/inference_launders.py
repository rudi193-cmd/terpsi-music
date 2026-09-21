"""A guard used once and walked around twice. NEVER IMPORTED.

This is the decoy against the *wrong implementation of guardedness*. A checker
that asks "does this module import `records.inference`?" clears this file: it
does import it, and calls it, on the harmless path. The two calls that matter
sit beside that one and never go near it.

The second is the tired-afternoon shape: a guarded call, and a retry underneath
it that quietly asks the cloud chain instead — which is the exact degradation
refusal 1's last sentence forbids.

`tools/providers.py` must report both direct calls as UNGUARDED and leave the
guarded one alone.
"""

from core.inference_router import chat, respond
from records.inference import through

SYSTEM = "You answer questions about a student's fee balance."
LOCAL_MODEL = "http://localhost:11434"


def blurb(atoms):
    """The alibi: one real, guarded call, on data nobody would object to."""
    answer = through(lambda: respond("Write the concert blurb.", atoms, ""),
                     classes=["PUBLIC"], endpoint=LOCAL_MODEL)
    return answer.text


def balance_note(student, atoms):
    text, _provider = respond(SYSTEM, atoms, student)
    return text


def balance_note_with_retry(student, atoms):
    try:
        return through(lambda: respond(SYSTEM, atoms, student),
                       classes=["FINANCIAL"], endpoint=LOCAL_MODEL).text
    except Exception:
        return chat(SYSTEM, student, mode="cloud")[0]
