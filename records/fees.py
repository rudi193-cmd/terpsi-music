"""Fees — the Ledger domain core: charges and payments in a lane, aid that is
invisible by construction, and no card number anywhere in the type system.

The capability map's finance section (§7) asks for a per-student ledger, payment
plans, tokenized payment, and **invisible financial aid** — *"waivers and
scholarships applied so that no student, and no other family, can tell who is on
assistance. Dignity is a design requirement, not a nicety."* §18 restates it as
*"fee waivers that are structurally invisible to peers."*

Four mechanisms, each answering a specific harm:

## 1 · The amount is born correct (the waiver is not a field)

`docs/survey/scout-18-finance-dignity.md` §2.1 verified the mechanic in
`cal-itp/benefits`, in government production: enrolment does not produce a list
of discounted riders that anyone at the point of service reads. It adds the
rider's tokenized funding source to a **concession group**, and the discount is
computed on the rail. The driver and the other riders observe an ordinary tap.

Here: a `Charge`'s amount is resolved from `Membership` in a `FeeGroup` by
`assess()`, and the charge is written already-correct. **There is no `waiver`
column on `Charge`, no `discount`, and no `standard_amount`** — the report's
corollary is the sharp half: *"there must be no place where the pre-waiver
amount and the post-waiver amount both appear, because the difference is the
disclosure."* So `assess()` returns one number and this module offers no
function that returns two.

The anti-pattern is equally verified and is built as a refusal below:
`OS4ED/openSIS-Classic`'s roster search filtered on *"Student Billing Balance
between X and Y"* (`functions/WidgetsFnc.php`). A staff-facing student search
whose filter is money enumerates the aided families in one query.

## 2 · Waiver status is `L5`, by rule 3 and not by policy

`docs/SENSITIVITY.md`'s third `L5` rule: *"any record whose rendering would
reveal a refusal… a media release refused, a **fee waiver taken**, a consent
withdrawn — is enforced and never shown."* §18 item 11 notes this was already
load-bearing on the fee-waiver requirement before anyone connected them.

`WAIVER` below is the descriptor, and `records/classify.py` — not this module —
decides the rung, so there is one classifier and this file states a fact about a
field rather than a second opinion. `serving.serve()` then refuses it to every
principal under every grant, including the director, including the subject.

## 3 · The aggregate is where it actually leaks

Also from the report: *"the export that leaks is not the roster, it is the
summary. 'Total fees collected, by section' over a drumline of eleven students,
published beside a total-owed figure, identifies the waiver."* `total()` routes
through `classify.aggregate`, which applies `SENSITIVITY.md` step 2a's
re-identification check with a **declared** suppression floor, and refuses to
hand over the number when the cohort is under it. The worked harm — a section of
three with one waiver — is a test.

## 4 · Tokenized only, and there is nowhere to put a PAN

§8's constraint and §10's PCI row: *"payment card data never enters the system —
hosted fields, tokens only, staying in PCI SAQ-A territory."* `Payment` carries
a `token_ref` and **has no field for a card number**, so the ordinary way to
store one raises `TypeError` at construction. The *interesting* attack is the
second one: a PAN pasted into the field that does exist. `__post_init__` refuses
any string field that looks like a card number — 13–19 digits passing Luhn — so
the smuggling path is closed too.

Its false positive is real and is the correct direction: a numeric reference of
that length which happens to satisfy Luhn is refused, and the fix is to write
the reference differently. Refusing a legitimate receipt number costs an
afternoon; accepting one PAN acquires PCI scope for the whole install.

**Read `docs/survey/scout-18-finance-dignity.md` §0 before quoting SAQ-A at
anybody.** That report could not reach `stripe.com` or the PCI SSC and records
the eligibility wording as `unknown` rather than asserting it. What this module
implements is *never touching card data*, which is the design constraint; which
SAQ a given install files is a question nobody here has read the standard for.

## Money is integer minor units, always

No floats. `cents` is an `int` in every type, and a construction that hands over
a `float` is refused rather than rounded: a balance that drifts by a cent is a
statement to a family that the program cannot count, and it arrives through
exactly one line of arithmetic.

## Rule 13, in the register that bills people

An errored charge or payment source is `UNKNOWN`, **never `$0`**. A zero
invented by a failure is either a bill (if it lands on the charges side) or a
shame (if it lands on the payments side and a family reads *"nothing paid"*).
`Balance.cents` raises rather than returning `None` for the same reason
`sending.SendList.__iter__` raises: `b.cents or 0` is one keystroke away and
reads as caution.

## Retention — recorded, not built

Not built here (§10's row is a season-boundary purge job). What the types carry
for it: `season` on `FeeGroup`, `Charge` and `Payment`, and dates on everything
— `created_at`, `valid_at`, `invalid_at`. A charge is never deleted; it is dated
closed, because a refund and a reversal are different facts and a deleted charge
cannot tell a successor treasurer which one happened.

Stdlib only. No network, no store, no model.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field as _field, fields as _fields, replace
from datetime import datetime
from enum import Enum
from typing import Callable, Optional, Sequence

from .classify import Descriptor, aggregate, classify
from .conflict import Escalation, Stake, halt, one_lane, refuse_to_rank
from .rungs import Rung


class CardData(Exception):
    """A value that looks like a card number reached a field of this module.

    Not a `ValueError`, because the caller needs to know what happened: the
    install's PCI posture depends on card data never entering the system, and a
    generic validation error reads as a formatting complaint.
    """


class NotDisclosable(Exception):
    """A number was asked for that the re-identification check did not clear."""


# --- the PAN refusal -------------------------------------------------------

#: A card number is 13–19 digits. Shorter numeric references (an invoice number,
#: a check number) are common and legitimate, so the window is deliberately not
#: "any long digit string."
_PAN_MIN, _PAN_MAX = 13, 19


def _luhn(digits: str) -> bool:
    """The check digit every card scheme uses. Cheap, and it is the whole test.

    Luhn alone would flag some non-card numbers; Luhn **plus** a 13–19 digit
    length is specific enough that a hit is far more likely to be a PAN than a
    coincidence, and the failure direction of a false positive is an afternoon
    rather than an audit.
    """
    total, parity = 0, len(digits) % 2
    for i, ch in enumerate(digits):
        n = int(ch)
        if i % 2 == parity:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


#: A run of 13–19 digits, optionally spaced or hyphenated in groups, not
#: adjacent to further digits. **Contiguous runs, not every digit in the
#: string**, and that is what keeps the check usable: a UUID's longest
#: all-digit run is twelve characters, so a lane id cannot trip it, while
#: `"tok_4111111111111111"` and `"4111 1111 1111 1111"` both do.
_RUN = re.compile(r"(?<![0-9])(?:[0-9][ -]?){%d,%d}(?![0-9])" % (_PAN_MIN, _PAN_MAX))


def looks_like_a_card_number(value: str) -> bool:
    """True when `value` contains a plausible PAN, separators and all.

    *Contains*, not *is*: the realistic way a card number arrives is inside
    something else — a memo line reading *"paid by card 4111 1111 1111 1111"*,
    or a token field somebody pasted the wrong half of.

    Public because the refusal should be testable directly and because a caller
    validating its own input before construction is the friendly order — this is
    not a secret the module keeps.
    """
    for run in _RUN.findall(str(value)):
        bare = "".join(ch for ch in run if ch.isdigit())
        if _PAN_MIN <= len(bare) <= _PAN_MAX and _luhn(bare):
            return True
    return False


def _refuse_card_data(obj) -> None:
    """Scan every string field of a frozen record for a PAN.

    Applied to the whole record rather than to one field, because the point is
    that there is nowhere to put one: closing only `token_ref` would leave the
    memo line open, and a memo line is where it would actually go.
    """
    for f in _fields(obj):
        value = getattr(obj, f.name)
        if isinstance(value, str) and looks_like_a_card_number(value):
            raise CardData(
                f"{f.name} carries what looks like a card number. Card data never "
                "enters this system — a token reference is what a payment carries, "
                "and there is no field here for a PAN (§8, §10's PCI row)."
            )


def _cents(value, what: str) -> int:
    """Integer minor units or a refusal. A float is not money."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(
            f"{what} is {value!r}; money is integer minor units here. A float "
            "balance drifts by a cent and tells a family the program cannot count."
        )
    return value


# --- the fee schedule, and where aid lives ---------------------------------


@dataclass(frozen=True)
class FeeGroup:
    """A band of the fee schedule. **Aid is membership in one of these.**

    There is no `is_aid` flag and no `discount` — a group is an amount for an
    activity, and the group a student is in is the only thing that differs. That
    is Cal-ITP's concession group with the processor removed: the resolution
    happens on the local hub, behind the egress gate, because achieving the
    dignity property by pushing the discount to a third party is the move §6 and
    refusal 1 exist to prevent.
    """

    group_id: str
    activity: str
    cents: int
    season: str

    def __post_init__(self):
        _cents(self.cents, f"fee for {self.activity!r}")
        if self.cents < 0:
            raise ValueError("a negative fee is a credit; write it as a payment")


@dataclass(frozen=True)
class Membership:
    """One student in one fee group, dated.

    `invalid_at` rather than a delete (refusal 3), which also gives Cal-ITP's
    membership expiry for free. **This record is `L5` when it is read as a
    status** — see `WAIVER` — and it is consulted by `assess()` and by nothing
    else in this module.
    """

    lane_id: str
    subject_id: str
    group_id: str
    valid_at: datetime
    created_at: datetime = _field(kw_only=True)
    invalid_at: Optional[datetime] = _field(default=None, kw_only=True)

    def live_at(self, when: datetime) -> bool:
        if when < self.valid_at:
            return False
        return self.invalid_at is None or when < self.invalid_at


#: The waiver status as a field, handed to the one classifier.
#:
#: `reveals_a_refusal=True` is the whole assertion, and it is a human's judgment
#: recorded here rather than a rung this module chose: `SENSITIVITY.md`'s `L5`
#: rule 3 names *"a fee waiver taken"* as its own example. `classify()` decides.
WAIVER = Descriptor("fee_waiver", identifies_a_person=True, category="money",
                    reveals_a_refusal=True)


#: A balance, as a field. `FINANCIAL` is `L4` in the class table, and the same
#: rung falls out of step 3 because money is one of its four familiar
#: categories — so this descriptor states the *facts* about the field and the
#: classifier states the rung, which is the arrangement `tools/registry.py`
#: exists to keep honest. A balance is not `L5`: a guardian is entitled to be
#: told what they owe, and the thing that must never render is *why it is what
#: it is*.
BALANCE = Descriptor("balance", identifies_a_person=True, category="money")


def waiver_rung() -> Optional[Rung]:
    """What the classifier makes of a waiver status. `L5`, and derived not typed."""
    return classify(WAIVER).rung


def balance_rung() -> Optional[Rung]:
    """What the classifier makes of a balance. `L4`, and derived not typed.

    Which matters at the read: `serving.serve()` gives an `L4` field to a
    principal holding a live edge **and** a purpose declared for the category on
    entry. A staff member with an attendance purpose does not see a balance on
    the same device ten minutes earlier, which is `SENSITIVITY.md`'s worked `L4`
    example with money substituted for the auto-injector.
    """
    return classify(BALANCE).rung


# --- charges ---------------------------------------------------------------


@dataclass(frozen=True)
class Charge:
    """One amount owed by one student, in that student's lane.

    Note the fields that are absent: no `waiver`, no `discount`, no
    `standard_cents`, no `original_cents`, no `aid`. A charge carries what is
    owed. The difference between what this student owes and what another one
    owes is not recorded anywhere, because the difference is the disclosure.
    """

    lane_id: str
    subject_id: str
    activity: str
    cents: int
    season: str
    valid_at: datetime
    created_at: datetime = _field(kw_only=True)
    invalid_at: Optional[datetime] = _field(default=None, kw_only=True)
    #: The event or item this charge is for — `referent.referent_id`, whose
    #: `kind` the DDL already lists as `Charge`. Optional because a season fee
    #: is not an event.
    referent_id: Optional[str] = _field(default=None, kw_only=True)

    def __post_init__(self):
        _cents(self.cents, f"charge for {self.activity!r}")
        _refuse_card_data(self)

    def live_at(self, when: datetime) -> bool:
        if when < self.valid_at:
            return False
        return self.invalid_at is None or when < self.invalid_at


class Source(Enum):
    DERIVED = "derived"
    UNKNOWN = "unknown"   # a source could not be consulted; NOT zero, NOT full price


@dataclass(frozen=True)
class Assessment:
    """The outcome of resolving a fee. A charge, or an honest `unknown`.

    **The failure this shape prevents is a bill.** If the membership source
    errors and the resolver falls back to the schedule's standard amount, a
    family on assistance is invoiced the full season fee by a network timeout.
    Falling back the other way is no better — it would hand aid out by accident
    and, worse, make the accident legible in the books. So there is no fallback:
    the charge is not written and somebody is told.
    """

    state: Source
    reason: str
    _charge: Optional[Charge] = None

    @property
    def charge(self) -> Charge:
        if self.state is not Source.DERIVED or self._charge is None:
            raise RuntimeError(
                f"the fee could not be resolved: {self.reason}. An unresolved fee is "
                "not the standard fee and it is not zero (rule 13)."
            )
        return self._charge


def assess(subject_id: str, lane_id: str, activity: str,
           groups: Sequence[FeeGroup],
           memberships: Sequence[Membership] | Callable[[], Sequence[Membership]],
           at: datetime, *, season: str) -> Assessment:
    """Resolve what this student owes for this activity, at this instant.

    **The charge is born correct.** The group is resolved first and its amount is
    the amount; there is no "standard fee then apply waiver" step, because that
    step is the thing that has to appear somewhere, and wherever it appears is
    where a volunteer reads it.

    `memberships` may be a callable, and a callable that raises yields `UNKNOWN`
    — the shape `sending.recipients` uses for the same reason.

    **Membership is universal and that is the dignity property.** Every student
    enrolled in the activity holds exactly one live membership, so a membership
    row's *existence* says nothing; only which group it names says anything, and
    that is `L5`. The tempting alternative — rows only for students on
    assistance, everyone else falling back to a standard band — makes the
    presence of the row the disclosure, which is the same defect as a `waiver`
    boolean with an extra join in front of it.

    So there is no fallback. No live membership is `UNKNOWN`, not the standard
    fee; more than one is `UNKNOWN` too, because choosing the lower would be the
    system granting aid and choosing the higher would be the system billing for
    it, and W-7 says a human decides.
    """
    if callable(memberships):
        try:
            found = tuple(memberships())
        except Exception as exc:  # noqa: BLE001 — any failure is unknown, not a price
            return Assessment(Source.UNKNOWN, f"membership source failed: {exc!r}")
    else:
        found = tuple(memberships)

    for_activity = [g for g in groups if g.activity == activity and g.season == season]
    if not for_activity:
        return Assessment(Source.UNKNOWN,
                          f"no fee band is declared for {activity!r} in {season}")

    live = {m.group_id for m in found
            if m.subject_id == subject_id and m.live_at(at)}
    bands = [g for g in for_activity if g.group_id in live]
    if not bands:
        return Assessment(
            Source.UNKNOWN,
            f"no live fee band for this student in {activity!r}; an unresolved band "
            "is not the standard fee, and a fallback would make the absence of a "
            "membership row mean something")
    if len(bands) > 1:
        return Assessment(
            Source.UNKNOWN,
            f"this student holds {len(bands)} live fee bands for {activity!r}; the "
            "lower would be the system granting aid and the higher would be the "
            "system billing for it (W-7)")
    return Assessment(
        Source.DERIVED,
        f"{activity!r} in {season} resolved from one fee band",
        Charge(lane_id, subject_id, activity, bands[0].cents, season, at,
               created_at=at))


# --- payments --------------------------------------------------------------


class Tender(Enum):
    """How money arrived. `CARD` names a **token**, never a number.

    Cash and check are here because `scout-18` §2.6's honest map ends there:
    *"the processor still sees that one family pays less… cash, checks and bank
    debit are the real sovereign rails."*
    """

    CARD_TOKEN = "card_token"
    BANK_DEBIT = "bank_debit"
    CASH = "cash"
    CHECK = "check"
    ADJUSTMENT = "adjustment"   # a correction, made by a named human


@dataclass(frozen=True)
class Payment:
    """Money received against a lane. **There is no field for a card number.**

    `token_ref` is an opaque reference issued by whatever took the money. A
    construction like `Payment(pan=…)` or `Payment(card_number=…)` raises
    `TypeError` because the parameter does not exist, and a PAN pasted into
    `token_ref`, `reference` or `memo` raises `CardData` because
    `__post_init__` looks (see `_refuse_card_data`).
    """

    lane_id: str
    subject_id: str
    cents: int
    tender: Tender
    at: datetime
    received_by: str
    season: str
    created_at: datetime = _field(kw_only=True)
    token_ref: Optional[str] = _field(default=None, kw_only=True)
    reference: Optional[str] = _field(default=None, kw_only=True)
    memo: str = _field(default="", kw_only=True)
    invalid_at: Optional[datetime] = _field(default=None, kw_only=True)
    #: Who reversed it, and why. Set by `reverse()` beside `invalid_at`: an
    #: ending nobody can answer for is the half of refusal 3 a bare date does
    #: not carry (`records/orders.py`'s `ended_by`, same argument).
    reversed_by: Optional[str] = _field(default=None, kw_only=True)
    reversal_reason: str = _field(default="", kw_only=True)

    def __post_init__(self):
        _cents(self.cents, "payment")
        if self.cents <= 0:
            raise ValueError(
                "a payment of nothing is not a payment; a reversal is its own "
                "dated record, not a negative one"
            )
        if self.tender is Tender.CARD_TOKEN and not (self.token_ref or "").strip():
            raise ValueError(
                "a card payment carries a token reference; if there is no token, "
                "the money did not arrive through a hosted field and this record "
                "is describing something else"
            )
        if not (self.received_by or "").strip():
            raise ValueError("a payment nobody received is not a payment (§7's audit)")
        _refuse_card_data(self)

    def live_at(self, when: datetime) -> bool:
        if when < self.at:
            return False
        return self.invalid_at is None or when < self.invalid_at


# --- the balance -----------------------------------------------------------


@dataclass(frozen=True)
class Balance:
    """What one lane owes at one instant, or an honest `unknown`.

    `cents` is a property that **raises** when the state is `UNKNOWN`. A `None`
    would be unwrapped with `or 0` by the second caller, and a zero balance
    printed to a guardian is either *"you owe nothing"* or *"you have paid
    nothing"* depending on which side failed — both of them wrong and one of
    them humiliating.
    """

    state: Source
    lane_id: str
    reason: str
    _cents: Optional[int] = None
    charges: int = 0
    payments: int = 0

    @property
    def cents(self) -> int:
        if self.state is not Source.DERIVED or self._cents is None:
            raise RuntimeError(
                f"balance is {self.state.value}, not derived: {self.reason}. An "
                "unknown balance is not zero (rule 13)."
            )
        return self._cents

    @property
    def owed(self) -> bool:
        return self.cents > 0


def balance(charges, payments, at: datetime,
            lane_id: Optional[str] = None) -> Balance:
    """Charges minus payments, in one lane, at one instant.

    Both arguments may be sequences or callables; a callable that raises yields
    `UNKNOWN` naming which side failed, because *"we could not read your
    payments"* and *"we could not read your charges"* are different apologies.

    One lane, by `conflict.one_lane`: a balance summed across two students is a
    lane-seal breach on the way to a ranking, and *"who owes the most"* is the
    query this module exists to make unavailable.
    """
    try:
        cs = tuple(charges() if callable(charges) else charges)
    except Exception as exc:  # noqa: BLE001
        return Balance(Source.UNKNOWN, lane_id or "",
                       f"charge source failed: {exc!r}")
    try:
        ps = tuple(payments() if callable(payments) else payments)
    except Exception as exc:  # noqa: BLE001
        return Balance(Source.UNKNOWN, lane_id or "",
                       f"payment source failed: {exc!r}")

    rows = tuple(cs) + tuple(ps)
    if not rows:
        if lane_id is None:
            return Balance(Source.UNKNOWN, "",
                           "no rows and no lane named; an empty result from an "
                           "unnamed lane is not a balance of zero")
        return Balance(Source.DERIVED, lane_id, "no charges and no payments", 0, 0, 0)

    lane = one_lane(rows, "a balance spanning lanes")
    if lane_id is not None and lane != lane_id:
        raise ValueError(f"rows are in {lane!r}, not the named lane {lane_id!r}")

    owed = sum(c.cents for c in cs if c.live_at(at))
    paid = sum(p.cents for p in ps if p.live_at(at))
    return Balance(Source.DERIVED, lane,
                   f"{len(cs)} charge(s) less {len(ps)} payment(s) at {at.isoformat()}",
                   owed - paid, owed, paid)


# --- the aggregate anyone can see ------------------------------------------


@dataclass(frozen=True)
class Total:
    """A program-level figure, carrying the rung its cohort earned it.

    `cents` raises unless the re-identification check passed. That is the
    difference between this and every finance dashboard: the number is not
    withheld by a permission somebody can hold, it is **unavailable** until the
    cohort is large enough that the number cannot be resolved to a family.
    """

    cents_if_servable: Optional[int]
    cohort: int
    floor: int
    rung: Optional[Rung]
    reason: str

    @property
    def servable(self) -> bool:
        return self.rung is Rung.L2 and self.cents_if_servable is not None

    @property
    def cents(self) -> int:
        if not self.servable:
            raise NotDisclosable(
                f"a total over a cohort of {self.cohort} against a declared floor of "
                f"{self.floor} is {self.rung}: {self.reason}. A section of three with "
                "one waiver is identified by its total."
            )
        return self.cents_if_servable


def total(charges: Sequence[Charge], *, floor: int, at: datetime) -> Total:
    """Sum charges across students, through the re-identification gate.

    This is the one function in the module that reads more than one lane, and
    it may because it returns a single integer with no subject list and no
    ordering. The protection it needs is the suppression floor, which the caller
    **declares** — `classify.aggregate` has no default and this does not add one.

    `FINANCIAL` is `L4`, so an unchecked total inherits `L4` and `Total.cents`
    refuses. Passing the check drops it to `L2`, which is the class table's
    `DERIVED_ANON` row behaving exactly as written.
    """
    live = [c for c in charges if c.live_at(at)]
    cohort = len({c.subject_id for c in live})
    c = aggregate("program_total", over=(Rung.L4,), cohort=cohort, floor=floor)
    amount = sum(x.cents for x in live)
    return Total(amount if c.rung is Rung.L2 else None, cohort, floor, c.rung, c.reason)


# --- refusal 6, in money's clothes -----------------------------------------


def allocate(what: str, *, among: Sequence[str], to_whom: str, at: datetime,
             considerations: Sequence[str] = (),
             scarce: bool = True) -> Escalation:
    """A limited slot, a scholarship, a place on a payment plan — **escalated.**

    Refusal 6 arrives here wearing money: *one scholarship and four applicants*
    is a priority between students however it is scored, and a sliding scale
    that produces an eligibility is a different thing from a rank that produces
    a winner. `scout-18` §3 M5 records that no open-source implementation of
    need-based allocation avoiding a ranking was found, and that where genuine
    scarcity remains the honest primitive is a lottery with a recorded seed —
    which is a decision this module does not make and a human might.

    Returns `conflict.Escalation`, which is **incapable of carrying an order**:
    `affects` is sorted for display and `considerations` is a frozenset, so what
    a named human receives is everything relevant with no arrow pointing at an
    answer.
    """
    stake = Stake.BETWEEN_WARDS if scarce and len(set(among)) > 1 \
        else Stake.WARD_VS_CONVENIENCE
    return halt(stake, decision=what, affects=among, to_whom=to_whom, at=at,
                considerations=considerations)


def rank_by_need(applicants: Sequence[str]) -> None:
    """There is no such ordering. Findable by name so it is not rewritten.

    The tempting version sorts by a need score, which is a durable rating of a
    family carried between decisions — refusal 4's shape as well as refusal 6's.
    """
    refuse_to_rank("a need ranking for aid", applicants)


def roster_by_balance(*_args, **_kwargs) -> None:
    """The openSIS widget, refused.

    `scout-18` §2.7 verified the anti-pattern in `OS4ED/openSIS-Classic`
    (`functions/WidgetsFnc.php`): a roster search filtered on *"Student Billing
    Balance between X and Y"*, computed as fees plus lunch transactions minus
    payments. Combine it with a waiver implemented as a reduced amount and any
    volunteer with roster access enumerates the aided families in one query.

    The report's instruction was to *build that query as a failing test*. This is
    the query, and the test is that it cannot run.
    """
    raise NotDisclosable(
        "no roster or search surface here accepts a monetary predicate. A student "
        "list filtered by balance is a list of who is behind, and a fee-group "
        "member must be indistinguishable from a student who simply owes less "
        "(§18 of the capability map; §7's refusal-is-indistinguishable-from-absence)."
    )


def plan_priority(students: Sequence[str]) -> None:
    """Payment-plan ordering. Also a priority between students.

    Separate from `rank_by_need` because the name a treasurer would reach for is
    different, and `practice.standings` established that a refusal nobody can
    find gets reimplemented locally on a busy afternoon.
    """
    refuse_to_rank("a payment-plan priority", students)


# --- corrections -----------------------------------------------------------


def reverse(payment: Payment, *, by: str, at: datetime, why: str) -> Payment:
    """Reverse a payment by **dating it closed**, with who and why on the row.

    Refusal 3 and rule 16 over the books: a deleted payment cannot tell a
    successor treasurer whether a family's money was returned or was never
    received, and those are the two facts an embezzlement question turns on.
    Nothing is mutated and nothing is removed — `balance()` stops counting it
    because it is no longer live at the instant asked about.

    **The offsetting posting is not written here**, deliberately.
    `scout-18` §2.3's finding is that the institutional book is a plain-text
    double-entry journal a person can read without this software, and that the
    per-student ledger stays in the lane-aware store with the journal as its
    reconciled aggregate. A second, private set of double-entry postings inside
    this module would be the vendored pair §16 forbids, with a treasurer's
    memory as its only reconciler.
    """
    if not (why or "").strip():
        raise ValueError("a reversal without a reason is not an audit trail")
    if not (by or "").strip():
        raise ValueError("a reversal nobody performed is not a disposition")
    if payment.invalid_at is not None:
        raise ValueError("this payment was already reversed")
    return replace(payment, invalid_at=at, reversed_by=by, reversal_reason=why)
