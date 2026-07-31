"""The control: the same call, routed through the guard. NEVER IMPORTED.

A checker that flagged this too would prove nothing — it would be a rule
against importing a router rather than a rule about refusal 1, and the first
person who needed a model would delete it.

`tools/providers.py` must find the reach, mark it guarded, and report no
finding.
"""

from core.inference_router import respond
from records.inference import through

SYSTEM = "You summarise a student's medical note for a director."
LOCAL_MODEL = "http://localhost:11434"


def summarise(note, atoms):
    answer = through(lambda: respond(SYSTEM, atoms, note),
                     classes=["HEALTH"], endpoint=LOCAL_MODEL)
    return answer.text
