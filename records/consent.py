"""§18 item 10: which consent model governs which surface.

§13 states the problem and both mechanisms already exist:

> *"SAFE's model is a data subject authorizing access to their own data, and
> this domain is an institution holding records about minors. A parent viewing
> their student's balance fits the session model cleanly. A director opening the
> roster at 6 a.m. is not the data subject and cannot be asked to re-consent on
> the students' behalf every morning; the consent that governs them is the
> guardian's, granted elsewhere and enforced by predicate. Both mechanisms are
> built. What is not written down is which one governs which surface, and **a
> system that guesses will eventually ask the wrong person.**"*

**The axis is not "is this the data subject."** That was the obvious reading and
it is wrong on §13's own example: a *parent* is not the data subject and fits the
session model cleanly. The axis is **whether this principal holds the authority
the consent is about**, and can therefore give it at the door:

* `self` and `guardian_of` **hold it**. Asking them is asking the right person,
  and SAFE's session-expiring model is correct — consent dies with the session
  and the app asks again tomorrow.
* `staff_of`, `director_of`, `judge_at`, `clinician_for` **exercise it**. The
  authority is a guardian's, granted elsewhere; asking the director to consent
  on forty students' behalf every morning is asking the wrong person, in a form
  that makes saying yes the only workable answer.

**This decides whom to ask, not what is served.** `serve()` decides what a
principal may be served and is the only gate; this routes a surface to a consent
mechanism. Conflating the two would put a second, weaker authorization path
beside the predicate — §16's shape, arriving as a convenience.

**And it is rung-dependent for the subject**, which falls out of §18 item 12
rather than being invented here. A minor holds the authority over their own
record up to `L3`; above that they do not, because W-4 says a ward may request
and never authorize. So the same principal on the same lane is governed by the
session model for a call time and by the delegated model for a diagnosis. The
cap is one rule and this is the second place it shows.

**The third state is not a default.** §13's failure is *asking the wrong person*,
and both wrong answers are bad in different directions: guessing `SESSION` asks
someone who may not hold the authority, and guessing `DELEGATED` asks nobody and
leans on a grant that may not exist. So an unrecognised relationship returns
`UNKNOWN` and the caller must refuse (rule 13).

Stdlib only. No network, no store, no session.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Sequence

from .rungs import Rung, at_least
from .serving import Edge
from .standing import SELF, SELF_CAP, is_self_edge, past_threshold

#: Kinds that *hold* the authority a consent is about.
HOLDS = frozenset({SELF, "guardian_of"})

#: Kinds that *exercise* an authority granted elsewhere.
EXERCISES = frozenset({"staff_of", "director_of", "judge_at", "clinician_for"})


class Model(Enum):
    SESSION = "session"      # ask this principal now; consent expires with the session
    DELEGATED = "delegated"  # do not ask; a predicate over a guardian's grant decides
    UNKNOWN = "unknown"      # cannot tell who holds it; refuse rather than ask (rule 13)


@dataclass(frozen=True)
class Governance:
    """Which mechanism governs, and the reason — so a surface can be audited."""

    model: Model
    reason: str
    via_edge: Optional[str] = None

    @property
    def may_ask(self) -> bool:
        """Whether a surface may put a consent prompt in front of this principal.

        `UNKNOWN` is deliberately **not** askable. The temptation is to prompt
        when unsure — a prompt feels conservative — but §13's named failure is
        asking the wrong person, and a prompt shown to someone who does not hold
        the authority manufactures a consent record that looks valid.
        """
        return self.model is Model.SESSION


def governs(rung: Optional[Rung], principal_id: str, subject_id: str,
            edges: Sequence[Edge], at: datetime, *,
            threshold: Optional[datetime] = None) -> Governance:
    """Which consent model governs this principal reading this subject at `at`.

    Takes the **rung** because the subject's own authority is capped (item 12),
    and takes `edges` rather than a role because §7's whole model is that
    permissions derive from dated relationships rather than being stamped on
    people. An expired edge governs nothing.
    """
    if rung is None:
        return Governance(Model.UNKNOWN,
                          "unclassified field; the governing consent cannot be "
                          "decided before the sensitivity is")

    live = [e for e in edges
            if e.principal_id == principal_id and e.subject_id == subject_id
            and e.live_at(at) and not (e.kind == SELF and not is_self_edge(e))]

    if not live:
        return Governance(Model.UNKNOWN,
                          "no live relationship to this subject; there is nobody "
                          "here to ask and no grant to evaluate")

    # A principal may hold more than one edge. Take the strongest claim to the
    # authority, because a guardian who is also a staff member is still a
    # guardian — the delegated path must not narrow someone who holds the thing
    # outright.
    for e in live:
        if e.kind not in HOLDS:
            continue
        if e.kind == SELF:
            if at_least(rung, Rung.L4) and not past_threshold(at, threshold):
                # Item 12's cap, arriving as a consent question. The subject does
                # not hold the authority here, so the guardian's grant governs
                # and the subject is not prompted.
                return Governance(
                    Model.DELEGATED,
                    f"the subject's own authority is capped at {SELF_CAP} before the "
                    f"W-6 threshold; at {rung} a guardian's grant governs (W-4)",
                    via_edge=e.kind)
            return Governance(
                Model.SESSION,
                f"the subject holds the authority over their own record at {rung}",
                via_edge=e.kind)
        return Governance(
            Model.SESSION,
            "a guardian holds the authority this consent is about and can give it "
            "at the door; SAFE's session model applies",
            via_edge=e.kind)

    for e in live:
        if e.kind in EXERCISES:
            return Governance(
                Model.DELEGATED,
                f"{e.kind} exercises an authority granted elsewhere; asking this "
                "principal to consent on the subject's behalf asks the wrong person",
                via_edge=e.kind)

    kinds = sorted({e.kind for e in live})
    return Governance(Model.UNKNOWN,
                      f"unrecognised relationship {kinds}; refusing rather than "
                      "guessing which side of the authority it falls on")
