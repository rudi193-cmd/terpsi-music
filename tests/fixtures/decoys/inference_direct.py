"""An inference path born unguarded. NEVER IMPORTED.

The plainest shape of the thing refusal 1 forbids: import the fleet's router,
call it, use the text. The provider label is returned and thrown away, so
whether a school hub's stopped local model just sent a medical note to a cloud
provider is not knowable from this file or from anything downstream of it.

`tools/providers.py` must report every call here as UNGUARDED.
"""

from core.inference_router import respond

SYSTEM = "You summarise a student's medical note for a director."


def summarise(note, atoms):
    text, _provider = respond(SYSTEM, atoms, note)
    return text


def summarise_two(note, atoms):
    # The label is not even bound. There is nothing left to assert on.
    return respond(SYSTEM, atoms, note)[0]
