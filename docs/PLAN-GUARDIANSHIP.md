# Acceptance for the dated-guardianship predicate

**Status:** plan, not a decision record. Three questions need a human and are
marked. Nothing here is built.

**This does not restate §7.1.** The mechanism — terminate by setting
`invalid_at`, never by removing the edge, with `created_at` immutable beside
it — is settled there and in refusal 3 of `CLAUDE.md`. What is missing is the
part that makes it checkable: the acceptance gates, the derivation that has to
sit on the send path, and the questions nobody has answered.

**Why this first.** A seal makes a send *accountable*. It does not make it
*safe*. If the only thing between a court-ordered contact restriction and a
live location disclosure about a minor is a director reading a send list at
9pm, the mechanism §7.1 describes is not yet doing any work. §7.1 says the
failure here is a safety failure rather than a bug, and that it will arrive
urgently; acceptance is what decides whether it arrives to something.

---

## 1. The part §7.1 implies and does not spell out

**The send list is derived, never stored.**

```
recipients(student, at) -> [guardian, ...]
```

Guardians whose edge is valid at that instant. No `recipients` field, no cached
list, no `notify_parents` column. A stored list is a second copy of the truth
and it drifts the moment an order arrives — the same objection §16 raises
against any pair without a middle, except here the middle would have to be a
human remembering.

This is the whole safety property, and it is why §7.1 insists the predicate
gates outbound sends and not only reads. A read gate that does not also derive
the send list is not protecting the thing that actually leaves.

**The handler takes no recipient.** The strongest form is not a check, it is a
missing parameter:

```python
def message_guardian(payload):
    # payload carries a student and a time. It has no "to" field, and cannot.
    for guardian in recipients(payload["student"], at=payload["ts"]):
        ...
```

You cannot send to a restricted guardian because there is nowhere to put one.
That is the same discipline §6 describes as the inner ring — not gated,
inexpressible — applied to a recipient rather than to a socket, and it is
checkable statically, so it holds on a path no test exercises.

## 2. Acceptance

Per rule 19: a guard that cannot be shown to fail has not been shown to work.
Each row is a test that attempts the forbidden act and asserts refusal.

| # | Assertion |
|---|---|
| G1 | A guardian restricted as of T is absent from `recipients(student, T+1)` |
| G2 | …and **present** in `recipients(student, T−1)`. History stays answerable |
| G3 | A future-dated restriction does not take effect early, and does take effect on the day, with no job run between |
| G4 | No student-scoped message handler declares or reads a recipient — static, over the source |
| G5 | The order dated in March and delivered in October: a June disclosure evaluates differently against `valid_at` and `created_at`, and both are retrievable |
| G6 | `created_at` is immutable — an update raises rather than silently rewriting when the system learned something |
| G7 | There is no delete path for a guardianship edge anywhere in the module |
| G8 | Reinstatement leaves the prior restriction readable in sequence |
| G9 | No grant is constructible over a group, a section, or a roster (§7.4 W-2) |
| G10 | `who_could_see(student, field, at)` answers with a reason, as a query rather than an investigation |
| G11 | A consent or guardianship backend that errored surfaces as `unknown`, never as "no restrictions" |

G4 and G7 are the two that hold when everything else is forgotten, because they
are properties of the source rather than of behaviour at runtime. G11 is
rule 13 applied to the one lookup where the failure mode is a send.

**And a companion assertion, because indistinguishability proves less than it
looks.** §7 already records that the resolver's refusal-indistinguishability
test would pass if the predicate returned nothing to anyone — every count zero,
every list empty, all equal. Any test here asserting a restricted guardian sees
nothing must sit beside one asserting an *entitled* guardian sees exactly what
they should. That defect shape has been found in this fleet's verification
apparatus rather than in its code.

## 3. What this changes about group sends

**A student-scoped group send is a grant over a group**, which §7.4 W-2 rules
invalid at issuance — *"the drumline" is not a scope; a name is* — and it is
exactly the shape that delivers a location disclosure to a restricted guardian,
because nobody derives a send list when they are addressing a class.

The split:

- A broadcast survives **only** for content with no student referent — a
  program-wide announcement, a booster meeting time. Nothing is derived
  per-ward because no ward is named.
- Anything student-scoped **decomposes into N single-ward sends**, each with
  its own derived recipients and its own lane entry. Forty families is forty
  derivations, not one.

That is more expensive and it is the point. It also lands W-3 naturally: a
shared event is two lane entries with one referent, so one rehearsal
notification to two students is two records. **That is a schema decision and it
becomes a migration if it waits**, which is the argument for doing it at the
first write rather than when it first matters.

---

## 4. Three questions that need a human

**4.1 Who can enter a restriction?** It arrives mid-season, from outside, and
the person who physically receives the paperwork is usually the front office,
not the director. If the director is the only authority, the mechanism is
slower than the fax machine and the gap is the dangerous window. If the front
office can enter it, that is a wide grant over every family in the program.
Neither answer is obviously right and the wrong one is a real harm either way.

**4.2 Is the existence of a restriction visible, and to whom?** A caption head
who does not know may hand a student's phone to the wrong adult at a
competition, which argues for staff visibility. W-3 and ordinary discretion
argue against. A middle position — staff see *"release only to the named
person"* without seeing why — may be available, but somebody has to decide it
rather than have it fall out of an implementation.

**4.3 Does a notification restriction imply a release restriction?** The same
order governs both and they are different systems. Coupling them means the
software takes on a physical-world responsibility it cannot discharge.
Separating them means two places to get it right.

## 5. What this does not cover

- **The software cannot stop anyone at the field gate.** It governs what it
  sends and what it serves. Physical release of a student is a human process
  with a human failure mode, and a system that implies otherwise is worse than
  one that says so.
- **Confidential address programs are not designed here.** Whether the address
  is suppressed or the whole guardian edge withheld is a different question
  from contact restriction and needs its own pass.
- **The timing channel is untouched.** §4.2 already records that a per-guardian
  send firing only on the days one parent has the student reconstructs a
  custody arrangement for the carrier. Deriving the right recipients does not
  fix that; sending on a cadence uncorrelated with the event is a separate
  control and belongs with the SMS work.
- **This assumes the predicate is reachable from the send path.** If the
  messaging surface sits outside the store that holds it, everything above is
  prose. Confirming that is step zero.

## 6. Sequencing

1. **The safety core.** The edge with both axes, no delete path, derived
   `recipients()`, and the G4 static check. G1, G2, G4, G6, G7, G11.
2. **Time.** Future dating, reinstatement, `who_could_see`. G3, G5, G8, G10.
3. **The ward rules.** Decompose student-scoped broadcasts, land the two-lane
   rule for shared events. G9 — and this one is a migration if it waits.

Step 1 is the part worth having before the case arrives.
