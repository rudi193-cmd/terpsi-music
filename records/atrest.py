"""At-rest sealing across the Zone A boundary: the envelope and the key hierarchy.

§9's foundation 3 is the one line on that list that is honest about being half
done — *"chain integrity and per-subject erasure are built; at-rest sealing
across the Zone A boundary is not."* This is the missing half, built to be
propagated (§9: *"what this app lands in foundation 1–5 is what every later
app inherits"*) rather than to be sufficient here.

**This is not `records/sealing.py`, and the collision is in the domain rather
than in the design.** That module is §8.2's human cascade — a machine answer is
a `draft` until a *named person* stands behind it, and `seal()` there takes a
signature and a date. Nothing there encrypts anything and nothing here asks a
human for anything. The verbs are kept apart on purpose: `seal_bytes()` and
`unseal()` live here, `seal()` and `reject()` live there, and neither module
imports the other.

---

## The hierarchy, and where it departs from §5

§5 draws it as four tiers:

    Org Root Key            — TPM/HSM-sealed on the hub, never exported
      └─ Group Keys (KEK)   — X25519 keypair per access circle
           └─ Record DEKs   — AES-256-GCM, one per record/blob
                └─ wrapped per entitled circle via HPKE

What is built here is three tiers, and each departure is a decision rather than
an omission. They are recorded in `docs/AT-REST.md` and carried to §18.

**1 · The middle tier is keyed by lane, not by circle.** §5's circles are
`Family:1234`, `Staff:Ensemble7`, `Judges:Event42` — sets of people *and, by
implication, sets of students*. A key held per circle seals every Ensemble 7
student's records under one key, which is rule 8's roster column moved down to
the key layer: destroying one student's key becomes impossible without
destroying seven others', and W-1's *separate storage, permissions, audit
trail* stops at the storage. So the key tier is **one lane, one key**, and
circles stay what they always were — an entitlement question about who may be
handed a lane key, decided by `records/serving.py`, never a key-derivation
question.

**2 · Lane keys are random and wrapped, never derived.** `HKDF(master,
info=lane_id)` is cheaper — no wrapping table, nothing to persist — and it is
disqualifying here, because a derived key is **recomputable from the master
forever**. Destroying it destroys nothing. §5's own erasure clause is the test
a derivation cannot pass: *"one member's history is deletable without touching
anyone else's."* A random lane key wrapped under the master is deletable by
destroying its one wrapping, and that is the only reason rotation and erasure
can both be true at once.

**3 · Wrapping is symmetric, because the asymmetric property is not needed at
this tier and the primitive is not present.** §5 says X25519 + HPKE, which buys
*wrap without the ability to unwrap* — a writer sealing for a circle it cannot
read. Inside Zone A the party doing the sealing is the party holding the
master, so the property is unused; and the accepted dependency
(`cryptography==41.0.7`, §18 item 15) carries no HPKE. Where the property is
genuinely needed is §5's *crossing to B/C* column, and **this module does not
build that column.** `records/receipts.py` records the same shape one tier
over: *"a deployment wants Ed25519 here."*

**4 · Fernet is the record primitive, not AES-256-GCM.** Same reason: it is
what the one accepted dependency carries, it is what the fleet's own key store
uses, and it is authenticated. It has no associated-data parameter, so the
binding §5 gets from GCM's AAD is done by putting the header **inside** the
authenticated plaintext — see `_bound()`. A relabelled envelope therefore fails
to open rather than opening into the wrong lane, which is `MISBOUND`.

**5 · Where the master key lives is not decided here and must not be.** §5 says
TPM/HSM-sealed on the hub. This is a core: it takes key material as an
argument, returns artifacts, and the caller persists. Nothing in this module
opens a file, and `tools/purity.py` is pointed at it.

---

## What rotation costs, and the thing everyone gets wrong

§5's rotation section is about circle membership. The mechanical half it does
not state is the one that decides whether rotation is affordable at all:

**Re-wrapping under a new master must not require resealing a single record.**
It does not, and the reason is structural rather than clever — a sealed payload
names the **lane key** that opened it and never names the master. `rewrap()`
touches the wrapping table and returns payloads byte-identical, which
`tests/test_atrest.py` asserts by comparing the objects rather than by trusting
this paragraph.

Two rotations, kept apart because they are different acts:

* `rewrap()` — master rotation. Every lane key is re-wrapped, no payload moves,
  no `key_id` changes.
* `rotate_lane_key()` — **forward-only** revocation, §5's cheap and honest
  option. A new lane key is minted and the old wrapping is *kept*, so records
  sealed last season still open. This is correct for the graduated senior's
  parent who legitimately saw last season's data.

`reseal()` is the expensive option and is deliberately a separate, named call:
§5 reserves full re-encryption of history for a custody order or a terminated
staff member, and a function you have to reach for is the shape that keeps it a
decision.

## Erasure, and the chain that has to survive it

§5's hardest paragraph is the one where a member's consent transitions are
links in a hash chain the whole corps depends on. `records/disclosure.py`
answered it by partitioning the chain per lane. This module answers the other
half: **destroying a lane's key makes the lane's payloads unreadable and leaves
the chain and its anchors verifying exactly as before**, because the chain
covers *decisions* and never payloads — `disclosure._digest` deliberately
hashes no payload — and the sealed bytes are not chain material.

`composes()` is the named middle for that pair (rule 12, this commit). It does
not assume the two compose; it checks the chain, checks the anchor, checks that
every payload for the lane is now unreadable, checks that the erasure is a
**dated act with a name and a reason**, and reports which of those failed.

**Refusal 3 is not violated by destroying key material, and the distinction is
the whole design.** *Never revoke by deleting* is about standing — guardianship
ends by `invalid_at` so a dated record survives. Here the key material is
genuinely destroyed, and the `Erasure` **row survives it**: who destroyed it,
when, why, and which key ids. A keyring whose wrappings vanished with no
`Erasure` beside them is `UNRECORDED`, which is a finding rather than a clean
erasure.

## Escrow is surfaced, not solved

§5 calls single-file key loss *"the failure mode that ends the program"* and
proposes Shamir shares across the director, a board administrator and a sealed
offline share, rehearsed annually. **None of that is decided, and inventing it
here would be a maintainer's decision taken by a module.** So this carries the
*shape* of a disposition and no policy: it does not say how many shares, who
holds them, or how often the drill runs. What it refuses to do is stay quiet.

A master with no recorded disposition is `ABSENT` — its own state, dated by its
absence, never folded into "fine" (rule 13). A disposition that exists and has
never been rehearsed is `UNKNOWN`, quoting §5 rather than judging it: *"an
untested restore is not a backup, and an untested key recovery is not escrow."*
And the rehearsal due date is **declared at issuance with no default**, which
is `records/dispositions.py`'s P-2 rule — *a default would let issuers stop
declaring*.

`tools/conform.py` reads `ABSENT` today, honestly, and will keep reading it
until a maintainer decides.

## What this is, in rule 18's words

**A mechanism and a ledger, not a gate.** Nothing routes through it, because
there is no store: §5 is explicit that a SOIL collection's `store.db` is not
described as encrypted at rest and that *"the box is sovereign" and "the box is
encrypted" are different claims and only the first is currently true.* Whether
the canonical store is sealed at rest is a deployment decision this module
makes **representable** and does not make. Calling it enforcement today would
be the exact thing rule 18 forbids.

Requires `cryptography` (the one declared dependency). The import is lazy, so a
box without it still imports `records` and then *refuses* rather than falling
back to something weaker — `records/receipts.py`'s `AsymmetricUnavailable`
argument, applied to a primitive where a silent downgrade would be worse.

No network. No filesystem.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Sequence, Tuple

from .disclosure import verify_against

#: The one scheme this build seals with. A string rather than an enum member on
#: purpose: a `Sealed` written by a later build naming `aes-gcm-v2` must read as
#: *a scheme this build cannot open*, not as corruption, and an enum would have
#: to grow a member for every scheme that will ever exist before it could say so.
FERNET_V1 = "fernet-v1"

#: Schemes this build can actually open, derived from the opener table below
#: rather than declared beside it.
OPENABLE: frozenset = frozenset({FERNET_V1})

#: Field separator inside the bound header. Nothing an id may contain.
_SEP = "\x1f"

#: Separates the bound header from the payload inside the ciphertext.
_MARK = b"\x00"

_HEADER_VERSION = "atrest-1"

#: A lane is one student's lane. Refusal 5 at the key layer: a key minted for
#: `"the drumline"` seals a set, and a set cannot be erased per subject.
_WILDCARDS = frozenset({
    "*", "all", "any", "every", "everyone", "the drumline", "drumline",
    "section", "ensemble", "band", "roster", "all lanes", "lanes",
})

#: Identities that are not a person. An erasure or an escrow decision by one of
#: these is refused — same list-shape as `records/sealing.py`, same reason.
_NOT_A_PERSON = frozenset({
    "system", "machine", "agent", "automation", "bot", "service",
    "the director", "the staff", "director", "staff", "admin", "role:director",
})


# --- the primitive seam -----------------------------------------------------


class PrimitiveUnavailable(Exception):
    """The sealing primitive is not usable on this box.

    Raised rather than degraded. A fall back to *store it in the clear* would
    make sealed and unsealed look identical at every call site, and the first
    place anyone would notice is a breach.
    """


def _fernet_primitives():
    """The one import of this repository's one dependency (§18 item 15).

    Lazy, so a box missing it still imports `records`, and then refuses. The
    `BaseException` catch is `records/receipts.py`'s, for its reason: an absent
    install raises `ImportError` and a broken wheel raises whatever its
    bindings panic with, which was observed to be neither `ImportError` nor
    `Exception`. Both are the same fact at this seam.
    """
    try:
        from cryptography.fernet import Fernet, InvalidToken
    except BaseException as exc:  # noqa: BLE001 — deliberate; see the docstring
        raise PrimitiveUnavailable(
            "at-rest sealing was asked for and its primitive is not usable on "
            "this box. The dependency is declared in requirements.txt, so this "
            "is a broken or absent install and not a reason to store a record "
            "in the clear"
        ) from exc
    return Fernet, InvalidToken


def available() -> bool:
    """Whether this box can seal at all. Read by `tools/conform.py`.

    Derived by attempting the import, never by assuming the requirements file
    was honoured — the same reason `records/receipts.py` derives its scheme
    list rather than declaring it.
    """
    try:
        _fernet_primitives()
    except PrimitiveUnavailable:
        return False
    return True


# --- ids --------------------------------------------------------------------


def _check_id(value: str, what: str) -> str:
    name = (value or "").strip()
    if not name:
        raise ValueError(f"a {what} cannot be blank")
    if _SEP in name or "\x00" in name:
        raise ValueError(
            f"a {what} cannot contain the header separator; an id that can "
            "carry one can forge the binding it is bound by"
        )
    return name


def _check_lane(lane_id: str) -> str:
    name = _check_id(lane_id, "lane id")
    if name.lower() in _WILDCARDS:
        raise ValueError(
            f"{lane_id!r} names a set, not a lane. One lane, one key (W-1): a "
            "key over a section cannot be destroyed for one student, which is "
            "the whole point of a per-lane key"
        )
    return name


def _mint(prefix: str) -> str:
    """A key id.

    **Not a digest of the key material.** An id anybody can recompute from a
    candidate key is an offline oracle for guessing it; the id's job is to name
    a key, and naming does not require knowing.
    """
    return f"{prefix}-{secrets.token_hex(8)}"


def _check_person(who: str, act: str) -> str:
    name = (who or "").strip()
    if not name:
        raise ValueError(f"{act} needs a name; an unsigned act is not an act")
    if name.lower() in _NOT_A_PERSON:
        raise ValueError(
            f"{who!r} is a role or a machine, not a person, and {act} is a "
            "decision a person makes"
        )
    return name


# --- keys -------------------------------------------------------------------


@dataclass(frozen=True)
class MasterKey:
    """The key that never touches a record.

    It wraps lane keys and does nothing else. `seal_bytes()` refuses one by
    type, so *the master sealed a record directly* is unwritable rather than
    merely discouraged.
    """

    key_id: str
    material: bytes

    def __post_init__(self):
        object.__setattr__(self, "key_id", _check_id(self.key_id, "key id"))
        if not self.material:
            raise ValueError("a master key with no material is not a key")

    def __repr__(self) -> str:
        # Key material is `L5` by `records/classify.py`'s first override rule:
        # never rendered to anyone. A dataclass repr in a traceback is a
        # rendering, and tracebacks end up in logs.
        return f"MasterKey(key_id={self.key_id!r}, material=<withheld>)"


@dataclass(frozen=True)
class LaneKey:
    """One lane's data key, unwrapped. Lives in memory and is never persisted."""

    lane_id: str
    key_id: str
    material: bytes
    scheme: str = FERNET_V1

    def __post_init__(self):
        object.__setattr__(self, "lane_id", _check_lane(self.lane_id))
        object.__setattr__(self, "key_id", _check_id(self.key_id, "key id"))
        object.__setattr__(self, "scheme", _check_id(self.scheme, "scheme"))
        if not self.material:
            raise ValueError("a lane key with no material is not a key")

    def __repr__(self) -> str:
        return (f"LaneKey(lane_id={self.lane_id!r}, key_id={self.key_id!r}, "
                f"scheme={self.scheme!r}, material=<withheld>)")


@dataclass(frozen=True)
class WrappedLaneKey:
    """What the caller persists: a lane key sealed under a master.

    Names the master it is wrapped under, so a rotation that has not reached
    this row reads as `MASTER_MISMATCH` rather than as a decryption failure.
    """

    lane_id: str
    key_id: str
    under_master: str
    scheme: str
    wrapped: bytes
    created_at: datetime


class KeyState(Enum):
    """Three facts about a key id, never one boolean."""

    HELD = "held"            # a wrapping exists
    DESTROYED = "destroyed"  # an erasure act names it, with a date and a reason
    UNKNOWN = "unknown"      # nothing here has heard of it — not the same fact


# --- the sealed artifact ----------------------------------------------------


@dataclass(frozen=True)
class Sealed:
    """One sealed payload. The caller persists it; this module never does.

    Names its lane, its key and its scheme, which is what makes rotation
    representable: a payload sealed under `lane-ben`'s first key still says so
    after the second is minted, and after the master is rotated twice.

    **Not an anchor.** `records/witness.py`'s anchor carries a digest, a count
    and a time and may therefore legitimately cross the egress boundary. This
    carries a lane id, so it may not: it sits inside Zone A, in the lane's own
    storage, where the lane id is not new information.
    """

    lane_id: str
    key_id: str
    scheme: str
    ciphertext: bytes
    sealed_at: datetime

    def __post_init__(self):
        object.__setattr__(self, "lane_id", _check_lane(self.lane_id))
        object.__setattr__(self, "key_id", _check_id(self.key_id, "key id"))
        object.__setattr__(self, "scheme", _check_id(self.scheme, "scheme"))
        if not self.ciphertext:
            raise ValueError("a sealed payload with no ciphertext seals nothing")


def _bound(lane_id: str, key_id: str, scheme: str) -> bytes:
    """The header sealed **inside** the ciphertext.

    Fernet has no associated-data parameter, so the context §5 would bind
    through AES-GCM's AAD is bound by authenticating it as plaintext. Editing
    `Sealed.lane_id` after the fact therefore produces a payload that opens to
    a header disagreeing with its own envelope, which is `MISBOUND` — a
    relabelling, distinct from corruption and distinct from a wrong key.
    """
    return _SEP.join((_HEADER_VERSION, lane_id, key_id, scheme)).encode("utf-8")


# --- erasure and escrow, as records -----------------------------------------


@dataclass(frozen=True)
class Erasure:
    """Destroying a lane's key material is an act with a date, a name, a reason.

    The key material goes; **this row does not.** Refusal 3 is about standing
    ending without a dated record, and that is what this prevents — the record
    of the erasure outlives the thing erased, so a court order arriving in
    March can be answered in October.
    """

    lane_id: str
    key_ids: Tuple[str, ...]
    at: datetime
    by: str
    reason: str


class EscrowState(Enum):
    """What is known about recovering a master, and nothing about what should be."""

    ABSENT = "absent"      # no disposition recorded — §5's program-ending failure
    UNKNOWN = "unknown"    # recorded and never rehearsed; §5 says that is not escrow
    RECORDED = "recorded"  # recorded and rehearsed, within its declared window
    STALE = "stale"        # rehearsed, and the declared next drill is overdue


@dataclass(frozen=True)
class EscrowDisposition:
    """The *shape* of an escrow decision. Deliberately carries no policy.

    It does not say how many shares, what threshold, who may hold one, or how
    often the drill runs — every one of those is a maintainer's decision and
    §5 leaves them open. What it will not accept is a disposition that declares
    nothing: a named decider, at least one holder, and a **declared** next
    rehearsal date with no default, which is `records/dispositions.py`'s P-2
    rule — *a default would let issuers stop declaring*.
    """

    master_key_id: str
    decided_at: datetime
    decided_by: str
    holders: Tuple[str, ...]
    next_rehearsal_due: datetime
    rehearsed_at: Optional[datetime] = None

    def __post_init__(self):
        object.__setattr__(self, "master_key_id",
                           _check_id(self.master_key_id, "key id"))
        object.__setattr__(self, "decided_by",
                           _check_person(self.decided_by, "an escrow disposition"))
        if not self.holders or not all((h or "").strip() for h in self.holders):
            raise ValueError(
                "an escrow disposition naming no holder records that a decision "
                "was made and not what it was"
            )
        if self.next_rehearsal_due <= self.decided_at:
            raise ValueError(
                "the next rehearsal must be declared, and in the future of the "
                "decision; there is no default interval here on purpose"
            )


# --- the keyring ------------------------------------------------------------


def _latest(dated: list):
    """The last of a dated, appended series — **ties broken by arrival**.

    `max(…, key=…)` returns the *first* maximal element, so a rehearsal
    recorded on the same day as the disposition it rehearses loses to the
    disposition and the drill reads as never having happened. Found by the test
    that rehearses at the moment of recording, which is what a first install
    would do.
    """
    if not dated:
        return None
    return max(((when, i, obj) for i, (when, obj) in enumerate(dated)))[2]


@dataclass(frozen=True)
class Keyring:
    """What the caller persists. **Holds no key material that is usable alone.**

    Wrappings are ciphertext under a master this object does not have; erasures
    and escrow dispositions carry no material at all. Copying a keyring without
    the master yields nothing, which is the property §5 wants from the box:
    *"turns 'agents can't carry it out' from a policy promise into a
    cryptographic one."*
    """

    wrappings: Tuple[WrappedLaneKey, ...] = ()
    erasures: Tuple[Erasure, ...] = ()
    escrow: Tuple[EscrowDisposition, ...] = ()

    def wrapping_for(self, key_id: str) -> Optional[WrappedLaneKey]:
        return next((w for w in self.wrappings if w.key_id == key_id), None)

    def keys_for(self, lane_id: str) -> Tuple[WrappedLaneKey, ...]:
        return tuple(w for w in self.wrappings if w.lane_id == lane_id)

    def erasure_for(self, key_id: str) -> Optional[Erasure]:
        return next((e for e in self.erasures if key_id in e.key_ids), None)

    def erasure_for_lane(self, lane_id: str) -> Optional[Erasure]:
        return _latest([(e.at, e) for e in self.erasures if e.lane_id == lane_id])

    def state_of(self, key_id: str) -> KeyState:
        """Held, destroyed, or unknown. The three are not one boolean: a key
        nobody ever minted and a key a named person destroyed on a date are
        different answers to a guardian asking why a record will not open."""
        if self.wrapping_for(key_id) is not None:
            return KeyState.HELD
        if self.erasure_for(key_id) is not None:
            return KeyState.DESTROYED
        return KeyState.UNKNOWN

    def escrow_for(self, master_key_id: str) -> Optional[EscrowDisposition]:
        return _latest([(d.decided_at, d) for d in self.escrow
                        if d.master_key_id == master_key_id])

    def masters(self) -> Tuple[str, ...]:
        """Every master any live wrapping depends on, derived from the rows."""
        return tuple(sorted({w.under_master for w in self.wrappings}))


# --- minting and wrapping ---------------------------------------------------


def _wrap(master: MasterKey, lane_key: LaneKey, at: datetime) -> WrappedLaneKey:
    Fernet, _ = _fernet_primitives()
    return WrappedLaneKey(
        lane_id=lane_key.lane_id, key_id=lane_key.key_id,
        under_master=master.key_id, scheme=lane_key.scheme,
        wrapped=Fernet(master.material).encrypt(lane_key.material),
        created_at=at)


def new_master(*, key_id: Optional[str] = None) -> MasterKey:
    """A fresh master. Its custody is the deployment's problem, not this one's."""
    Fernet, _ = _fernet_primitives()
    return MasterKey(key_id or _mint("master"), Fernet.generate_key())


def open_lane_key(keyring: Keyring, *, lane_id: str, master: MasterKey,
                  at: datetime, key_id: Optional[str] = None,
                  ) -> Tuple[Keyring, LaneKey]:
    """Mint a lane's data key and wrap it under the master.

    Returns the new keyring **and** the unwrapped key, because the caller needs
    the second to seal with and must persist only the first. The key material
    is random rather than derived from `(master, lane_id)`, and the docstring
    at the top of this module is where that decision is argued.
    """
    Fernet, _ = _fernet_primitives()
    lane = _check_lane(lane_id)
    kid = _check_id(key_id, "key id") if key_id else _mint("lane")
    if keyring.state_of(kid) is not KeyState.UNKNOWN:
        raise ValueError(
            f"key id {kid!r} is already known to this keyring; reusing one "
            "makes two payloads name the same key and one of them wrong"
        )
    lane_key = LaneKey(lane, kid, Fernet.generate_key())
    return (Keyring(keyring.wrappings + (_wrap(master, lane_key, at),),
                    keyring.erasures, keyring.escrow),
            lane_key)


class KeyUnavailable(Exception):
    """No usable lane key, and *which* kind of no is the payload of this error."""

    def __init__(self, state: "Readable", reason: str,
                 erasure: Optional[Erasure] = None):
        super().__init__(reason)
        self.state = state
        self.reason = reason
        self.erasure = erasure


def unwrap(keyring: Keyring, *, key_id: str, master: MasterKey) -> LaneKey:
    """The one place master key material is used. Raises `KeyUnavailable`.

    It raises rather than returning `None` because the three ways this fails
    are three different facts and a `None` would flatten them — which is the
    shape rule 13 exists to forbid.
    """
    Fernet, InvalidToken = _fernet_primitives()
    state = keyring.state_of(key_id)
    if state is KeyState.DESTROYED:
        erasure = keyring.erasure_for(key_id)
        raise KeyUnavailable(
            Readable.KEY_DESTROYED,
            f"{key_id} was destroyed by {erasure.by} on "
            f"{erasure.at.date().isoformat()}: {erasure.reason}", erasure)
    if state is KeyState.UNKNOWN:
        raise KeyUnavailable(
            Readable.KEY_UNKNOWN,
            f"no wrapping and no erasure names {key_id}; this keyring has never "
            "heard of it, which is not the same as it having been destroyed")
    wrapping = keyring.wrapping_for(key_id)
    if wrapping.under_master != master.key_id:
        raise KeyUnavailable(
            Readable.MASTER_MISMATCH,
            f"{key_id} is wrapped under {wrapping.under_master} and the master "
            f"offered is {master.key_id}; a rotation has not reached this row")
    try:
        material = Fernet(master.material).decrypt(wrapping.wrapped)
    except InvalidToken:
        raise KeyUnavailable(
            Readable.UNREADABLE,
            f"the wrapping for {key_id} names {wrapping.under_master} and does "
            "not open under it; the wrapping or the master is not what it says"
        ) from None
    return LaneKey(wrapping.lane_id, key_id, material, wrapping.scheme)


# --- sealing ----------------------------------------------------------------


def seal_bytes(payload: bytes, *, lane_key: LaneKey, at: datetime) -> Sealed:
    """Seal one payload for one lane. The caller persists the result.

    **The master is refused by type.** §5's first line is that the root key
    never leaves the hardware and never touches a record; a hierarchy where the
    top key can also be used directly is one where somebody eventually will.
    """
    Fernet, _ = _fernet_primitives()
    if isinstance(lane_key, MasterKey):
        raise TypeError(
            "the master key never touches a record (§5). Wrap a lane key under "
            "it and seal with that — one lane, one key"
        )
    if not isinstance(lane_key, LaneKey):
        raise TypeError("seal_bytes() needs a LaneKey")
    if not isinstance(payload, (bytes, bytearray)):
        raise TypeError(
            "seal_bytes() takes bytes; encoding is the caller's decision and "
            "guessing it here would put a charset in the ciphertext")
    if lane_key.scheme not in OPENABLE:
        raise ValueError(
            f"this build cannot seal under {lane_key.scheme!r}; it seals under "
            f"{sorted(OPENABLE)}")
    header = _bound(lane_key.lane_id, lane_key.key_id, lane_key.scheme)
    body = header + _MARK + bytes(payload)
    return Sealed(lane_id=lane_key.lane_id, key_id=lane_key.key_id,
                  scheme=lane_key.scheme,
                  ciphertext=Fernet(lane_key.material).encrypt(body),
                  sealed_at=at)


class Readable(Enum):
    """Why a sealed payload did or did not open. **Never one boolean.**

    The three §5 forces apart are `UNREADABLE`, `KEY_DESTROYED` and
    `KEY_UNKNOWN`: a payload that fails its MAC is a tampering or a wrong key;
    a payload whose key a named person destroyed on a date is an erasure that
    worked; a payload naming a key nothing has heard of is a keyring that is
    incomplete or a payload from somewhere else. Collapsing them into *could
    not read it* answers a guardian's question with the one word that is never
    true.

    Three more are here because they are also distinct facts rather than
    flavours of failure — `MISBOUND` is a relabelling the MAC caught,
    `MASTER_MISMATCH` is a rotation that has not landed, and `SCHEME_UNKNOWN`
    is a payload from a later build, which must not read as corruption.
    """

    OPENED = "opened"
    UNREADABLE = "unreadable"            # held key, ciphertext fails authentication
    MISBOUND = "misbound"                # authenticates, sealed for another context
    KEY_DESTROYED = "key_destroyed"      # a dated erasure act
    KEY_UNKNOWN = "key_unknown"          # nothing here knows this key id
    MASTER_MISMATCH = "master_mismatch"  # wrapped under a master not offered
    SCHEME_UNKNOWN = "scheme_unknown"    # a scheme this build cannot open


@dataclass(frozen=True)
class Opening:
    """The result of trying to unseal. Carries the plaintext only on success."""

    state: Readable
    reason: str
    plaintext: Optional[bytes] = None
    erasure: Optional[Erasure] = None

    @property
    def opened(self) -> bool:
        return self.state is Readable.OPENED

    def __repr__(self) -> str:
        return (f"Opening(state={self.state.value!r}, reason={self.reason!r}, "
                f"plaintext={'<withheld>' if self.plaintext is not None else None})")


class Agreement(Enum):
    """Whether a payload's `(key_id, scheme, lane)` and the keyring agree."""

    AGREES = "agrees"
    SCHEME_DIVERGED = "scheme_diverged"  # the keyring's key is for another scheme
    LANE_DIVERGED = "lane_diverged"      # the key id is bound to another lane
    KEY_DESTROYED = "key_destroyed"
    KEY_UNKNOWN = "key_unknown"


def reconcile(sealed: Sealed, keyring: Keyring) -> Tuple[Agreement, str]:
    """**Rule 12's middle for the key-id ↔ scheme pair**, named in this commit.

    A sealed payload declares a key id and a scheme; a keyring holds a key id
    and a scheme. That is a pair, and the failure mode of an unmiddled pair is
    the one this repository keeps finding: nobody compares them, the code tries
    the key, and a mismatch surfaces as a decryption failure indistinguishable
    from tampering. So the comparison happens **before** any ciphertext is
    touched, and `unseal()` routes through it — this is enforcement on that
    path, not a ledger beside it.
    """
    state = keyring.state_of(sealed.key_id)
    if state is KeyState.DESTROYED:
        e = keyring.erasure_for(sealed.key_id)
        return (Agreement.KEY_DESTROYED,
                f"{sealed.key_id} was destroyed by {e.by} on "
                f"{e.at.date().isoformat()}: {e.reason}")
    if state is KeyState.UNKNOWN:
        return (Agreement.KEY_UNKNOWN,
                f"this keyring has never heard of {sealed.key_id}")
    w = keyring.wrapping_for(sealed.key_id)
    if w.scheme != sealed.scheme:
        return (Agreement.SCHEME_DIVERGED,
                f"the payload names scheme {sealed.scheme!r} and the key is held "
                f"for {w.scheme!r}; one of the two moved without the other")
    if w.lane_id != sealed.lane_id:
        return (Agreement.LANE_DIVERGED,
                f"the payload names lane {sealed.lane_id!r} and {sealed.key_id} "
                f"belongs to {w.lane_id!r}; one lane, one key (W-1)")
    return (Agreement.AGREES,
            f"{sealed.key_id} is held for {w.lane_id} under {w.scheme}")


def unseal_with(sealed: Sealed, *, lane_key: LaneKey) -> Opening:
    """Open a payload with a lane key the caller already holds.

    The binding check is the load-bearing part here, because a caller on this
    path has no keyring to catch a relabelling for it.
    """
    Fernet, InvalidToken = _fernet_primitives()
    if sealed.scheme not in OPENABLE:
        return Opening(Readable.SCHEME_UNKNOWN,
                       f"this build opens {sorted(OPENABLE)} and the payload "
                       f"names {sealed.scheme!r}; that is a payload from another "
                       "build, not a damaged one")
    try:
        body = Fernet(lane_key.material).decrypt(sealed.ciphertext)
    except InvalidToken:
        return Opening(Readable.UNREADABLE,
                       "the ciphertext does not authenticate under this key: it "
                       "was altered, or the key is not the one it was sealed with")
    header, _, plaintext = body.partition(_MARK)
    expected = _bound(sealed.lane_id, sealed.key_id, sealed.scheme)
    if header != expected:
        return Opening(Readable.MISBOUND,
                       "the payload authenticates and was sealed for a different "
                       "lane, key or scheme than the one it is filed under; the "
                       "envelope was relabelled")
    return Opening(Readable.OPENED, f"opened for {sealed.lane_id}", plaintext)


def unseal(sealed: Sealed, *, keyring: Keyring,
           master: Optional[MasterKey] = None) -> Opening:
    """Open a payload, going through the keyring and the master.

    With no master, this answers everything the keyring alone can answer —
    destroyed, unknown, diverged — and reports `MASTER_MISMATCH` rather than
    guessing for the rest. An answer of *unreadable* obtained by not trying is
    the absence-as-a-result shape rule 13 forbids.
    """
    if sealed.scheme not in OPENABLE:
        return Opening(Readable.SCHEME_UNKNOWN,
                       f"this build opens {sorted(OPENABLE)} and the payload "
                       f"names {sealed.scheme!r}; that is a payload from another "
                       "build, not a damaged one")
    agreement, why = reconcile(sealed, keyring)
    if agreement is Agreement.KEY_DESTROYED:
        return Opening(Readable.KEY_DESTROYED, why,
                       erasure=keyring.erasure_for(sealed.key_id))
    if agreement is Agreement.KEY_UNKNOWN:
        return Opening(Readable.KEY_UNKNOWN, why)
    if agreement in (Agreement.SCHEME_DIVERGED, Agreement.LANE_DIVERGED):
        return Opening(Readable.MISBOUND, why)
    if master is None:
        w = keyring.wrapping_for(sealed.key_id)
        return Opening(Readable.MASTER_MISMATCH,
                       f"{sealed.key_id} is held under {w.under_master} and no "
                       "master was offered; the key is available and was not asked for")
    try:
        lane_key = unwrap(keyring, key_id=sealed.key_id, master=master)
    except KeyUnavailable as exc:
        return Opening(exc.state, exc.reason, erasure=exc.erasure)
    return unseal_with(sealed, lane_key=lane_key)


# --- rotation ---------------------------------------------------------------


def rewrap(keyring: Keyring, *, was: MasterKey, now: MasterKey,
           at: datetime) -> Keyring:
    """Rotate the master. **No payload is resealed and no key id changes.**

    §5's rotation section is about people; this is the mechanical half it does
    not state, and it is the thing everyone gets wrong. A sealed payload names
    the *lane key*, so a new master is a new wrapping and nothing else — the
    cost of rotating is the number of lanes, not the number of records.

    Note what it does **not** carry forward: escrow. The new master has no
    recorded disposition, so `escrow_state()` reads `ABSENT` for it the moment
    this returns. That is correct and deliberate — the shares held for the old
    master do not reconstruct the new one, and a rotation that silently
    inherited the old disposition would be the most dangerous kind of quiet.
    """
    if was.key_id == now.key_id:
        raise ValueError(
            "rotating a master onto its own id leaves nothing able to tell the "
            "two apart; a rotation needs a new name")
    out = []
    rotated = 0
    for w in keyring.wrappings:
        if w.under_master != was.key_id:
            out.append(w)
            continue
        lane_key = unwrap(keyring, key_id=w.key_id, master=was)
        out.append(_wrap(now, lane_key, at))
        rotated += 1
    # A rewrap that matched no wrapping is a silent no-op: it returns a keyring
    # still wrapped under whatever it already was, having moved nothing to `now`.
    # An operator rotating off a compromised master who offered the wrong `was`
    # (a stale variable, the wrong key file) would read that as success, then
    # either destroy the old master — silent data loss — or keep trusting a
    # revocation that never happened. So it refuses, exactly as destroy() and
    # rotate_lane_key() refuse an act that would change nothing. The legitimate
    # incremental case (a keyring split across masters) still rotates, because it
    # has at least one wrapping under `was`; only the change-nothing call raises.
    if rotated == 0:
        raise ValueError(
            f"no wrapping is held under master {was.key_id!r}, so this rewrap "
            "would rotate nothing and hand back a keyring still wrapped under "
            "whatever it already was. Offer the master the wrappings are "
            "actually under; a rotation that changes nothing is the silent no-op "
            "destroy() and rotate_lane_key() both refuse")
    return Keyring(tuple(out), keyring.erasures, keyring.escrow)


def rotate_lane_key(keyring: Keyring, *, lane_id: str, master: MasterKey,
                    at: datetime, key_id: Optional[str] = None,
                    ) -> Tuple[Keyring, LaneKey]:
    """Mint a new key for a lane and **keep the old one**.

    §5's *forward-only revocation*: cheap, honest, and correct for most cases,
    because *"a graduated senior's parent legitimately saw last season's
    data."* Records sealed under the old key still open. Making history
    unreadable is `reseal()` plus `destroy()`, which are separate calls on
    purpose — §5 reserves that for a custody order or a terminated staff member.
    """
    if not keyring.keys_for(lane_id):
        raise ValueError(
            f"lane {lane_id!r} has no key to rotate; open_lane_key() first — a "
            "rotation that quietly mints a first key hides whether one existed")
    return open_lane_key(keyring, lane_id=lane_id, master=master, at=at,
                         key_id=key_id)


def reseal(items: Sequence[Sealed], *, from_key: LaneKey, to_key: LaneKey,
           at: datetime) -> Tuple[Sealed, ...]:
    """Re-encrypt history under a new lane key. **The expensive option.**

    A separate, named call rather than a flag on rotation, because §5 reserves
    full re-encryption for genuine incidents and a function somebody has to
    reach for stays a decision. Refuses across lanes: resealing lane A's
    records under lane B's key is the roster column arriving by migration.
    """
    if from_key.lane_id != to_key.lane_id:
        raise ValueError(
            "resealing across lanes would put two students' records under one "
            "key; one lane, one key (W-1)")
    if from_key.key_id == to_key.key_id:
        raise ValueError("resealing under the same key is not a reseal")
    out = []
    for s in items:
        if s.key_id != from_key.key_id:
            raise ValueError(
                f"{s.key_id} is not the key being resealed from; a reseal that "
                "skipped a payload would leave history half-readable and look done")
        got = unseal_with(s, lane_key=from_key)
        if not got.opened:
            raise ValueError(
                f"a payload did not open and cannot be resealed: {got.state.value} "
                f"— {got.reason}")
        out.append(seal_bytes(got.plaintext, lane_key=to_key, at=at))
    return tuple(out)


# --- erasure ----------------------------------------------------------------


def destroy(keyring: Keyring, *, lane_id: str, at: datetime, by: str,
            reason: str) -> Keyring:
    """Destroy a lane's key material. **The record of the act survives it.**

    Per-subject erasure, §5: one member's history goes without touching anyone
    else's. Every wrapping for the lane is dropped and an `Erasure` naming the
    key ids, the person, the date and the reason takes their place — so the
    keyring can still answer *why will this not open*, which is the difference
    between an erasure and a loss.
    """
    lane = _check_lane(lane_id)
    who = _check_person(by, "an erasure")
    if not (reason or "").strip():
        raise ValueError(
            "an erasure without a reason is not a disposition (I-6); the row "
            "that outlives the key is the only thing left to read")
    doomed = keyring.keys_for(lane)
    if not doomed:
        raise ValueError(
            f"lane {lane!r} holds no key to destroy. An erasure recorded against "
            "nothing reads afterwards as if something was erased")
    kept = tuple(w for w in keyring.wrappings if w.lane_id != lane)
    erasure = Erasure(lane, tuple(w.key_id for w in doomed), at, who, reason)
    return Keyring(kept, keyring.erasures + (erasure,), keyring.escrow)


class Composition(Enum):
    """How an erasure and a hash chain stand together."""

    COMPOSES = "composes"                  # payloads unreadable, chain and anchor intact
    CHAIN_BROKEN = "chain_broken"          # the erasure took the chain with it
    ERASURE_INCOMPLETE = "erasure_incomplete"  # recorded, and something still opens
    UNRECORDED = "unrecorded"              # wrappings gone with no dated act
    NOT_ERASED = "not_erased"              # keys still held; nothing was erased


@dataclass(frozen=True)
class Erasability:
    """What `composes()` found, with the counts it derived rather than assumed."""

    state: Composition
    reason: str
    erasure: Optional[Erasure] = None
    chain_ok: bool = False
    chain_reason: str = ""
    checked: int = 0
    unreadable: int = 0
    still_readable: int = 0

    @property
    def composes(self) -> bool:
        return self.state is Composition.COMPOSES


def composes(ledger, keyring: Keyring, *, lane_id: str,
             sealed: Sequence[Sealed] = (), master: Optional[MasterKey] = None,
             anchor: Optional[tuple] = None) -> Erasability:
    """**Rule 12's middle for the erasure ↔ chain pair**, named in this commit.

    §5 calls the per-subject partition the resolution and stops there. The
    claim that actually has to hold is the composite one: *destroying a lane's
    key renders its sealed payloads unreadable **while the chain and the
    anchors still verify.*** Two mechanisms, one claim, and nothing was
    checking that the claim survived them both.

    It holds structurally rather than by care — `records/disclosure.py` hashes
    a decision and deliberately never the payload, so key material is not chain
    material — but *structurally* is exactly the kind of reasoning that stops
    being true after a refactor nobody connected to it. So this checks:

    * the lane's chain verifies, and verifies against its anchor if one is given
    * every sealed payload for the lane fails to open, with `KEY_DESTROYED`
    * the erasure is a dated act with a name and a reason

    and reports which of those did not hold rather than a boolean.
    """
    log = ledger.log_for(lane_id)
    chain_ok, chain_why = log.verify()
    if chain_ok and anchor is not None:
        chain_ok, chain_why = verify_against(log, anchor)

    erasure = keyring.erasure_for_lane(lane_id)
    held = keyring.keys_for(lane_id)
    mine = [s for s in sealed if s.lane_id == lane_id]

    if master is not None:
        openings = [unseal(s, keyring=keyring, master=master) for s in mine]
        still = [o for o in openings if o.opened]
        gone = [o for o in openings if o.state is Readable.KEY_DESTROYED]
        how = "each payload was attempted against the keyring and the master"
    else:
        # No ciphertext is touched, so nothing is reported as having opened.
        # Saying *this one opened* on the strength of a table entry is the
        # absence-rendered-as-a-result shape rule 13 forbids, in the direction
        # that flatters the erasure.
        still = [s for s in mine if keyring.state_of(s.key_id) is KeyState.HELD]
        gone = [s for s in mine if keyring.state_of(s.key_id) is KeyState.DESTROYED]
        how = ("no master was offered, so the keyring's own state was read and "
               "no ciphertext was attempted")
    counts = dict(checked=len(mine), unreadable=len(gone), still_readable=len(still))

    if erasure is None:
        if held:
            return Erasability(
                Composition.NOT_ERASED,
                f"lane {lane_id} still holds {len(held)} key(s) and no erasure is "
                "recorded; nothing has been erased",
                None, chain_ok, chain_why, **counts)
        return Erasability(
            Composition.UNRECORDED,
            f"lane {lane_id} holds no key and no dated erasure names it. A key "
            "that vanished without a record is indistinguishable from one that "
            "was lost, which is the fact a guardian is owed",
            None, chain_ok, chain_why, **counts)

    # Payloads before wrappings, because a payload that still opens is the
    # stronger evidence and the one a guardian would find: a leftover wrapping
    # is a housekeeping defect, a readable record after an erasure is the
    # erasure not having happened.
    if still:
        return Erasability(
            Composition.ERASURE_INCOMPLETE,
            f"{len(still)} payload(s) for {lane_id} still readable after the "
            f"erasure ({how})",
            erasure, chain_ok, chain_why, **counts)
    if held:
        return Erasability(
            Composition.ERASURE_INCOMPLETE,
            f"an erasure is recorded for {lane_id} and {len(held)} wrapping(s) "
            "remain; a partial erasure reads as a whole one",
            erasure, chain_ok, chain_why, **counts)
    if not chain_ok:
        return Erasability(
            Composition.CHAIN_BROKEN,
            f"the payloads are unreadable and the chain no longer verifies: "
            f"{chain_why}. §5's resolution requires both",
            erasure, chain_ok, chain_why, **counts)
    return Erasability(
        Composition.COMPOSES,
        f"{len(gone)} payload(s) unreadable, {how}; {chain_why}",
        erasure, chain_ok, chain_why, **counts)


# --- escrow -----------------------------------------------------------------


def record_escrow(keyring: Keyring, disposition: EscrowDisposition) -> Keyring:
    """Record an escrow decision. This module does not decide what it should say."""
    return Keyring(keyring.wrappings, keyring.erasures,
                   keyring.escrow + (disposition,))


def rehearse(keyring: Keyring, *, master_key_id: str, at: datetime, by: str,
             next_due: datetime) -> Keyring:
    """Record a recovery drill. §5: *an untested key recovery is not escrow.*

    The next drill's date is declared here too, for the same reason it was
    declared at issuance — a rehearsal that does not say when the next one is
    due leaves the disposition indefinitely fresh.
    """
    current = keyring.escrow_for(master_key_id)
    if current is None:
        raise ValueError(
            f"no escrow disposition is recorded for {master_key_id}; a rehearsal "
            "of nothing is the strongest possible claim about the weakest state")
    who = _check_person(by, "a recovery rehearsal")
    if next_due <= at:
        raise ValueError("the next rehearsal must be declared, and in the future")
    done = EscrowDisposition(
        master_key_id=current.master_key_id, decided_at=at, decided_by=who,
        holders=current.holders, next_rehearsal_due=next_due, rehearsed_at=at)
    return record_escrow(keyring, done)


def escrow_state(keyring: Keyring, *, master_key_id: str,
                 at: datetime) -> Tuple[EscrowState, str]:
    """What is known about recovering this master. **Absence is its own state.**

    §5: *"a single file loss destroys every secret in the box, irrecoverably,
    by design… for an organization holding minors' education records it is
    not"* an acceptable trade. Nothing here fixes that. What it refuses to do
    is let a store with no recorded disposition read the same as one with a
    rehearsed disposition, which is rules 13 and 15 together: silence is not an
    answer, and the disposition is dated.
    """
    d = keyring.escrow_for(master_key_id)
    if d is None:
        return (EscrowState.ABSENT,
                f"no escrow disposition is recorded for {master_key_id}. §5 names "
                "single-file key loss as the failure that ends the program; this "
                "is that state, reported rather than assumed away")
    if d.rehearsed_at is None:
        return (EscrowState.UNKNOWN,
                f"a disposition was recorded by {d.decided_by} on "
                f"{d.decided_at.date().isoformat()} naming {len(d.holders)} "
                f"holder(s) and has never been rehearsed. §5: an untested key "
                "recovery is not escrow")
    if at >= d.next_rehearsal_due:
        return (EscrowState.STALE,
                f"last rehearsed {d.rehearsed_at.date().isoformat()}; the next "
                f"drill was declared due {d.next_rehearsal_due.date().isoformat()} "
                "and has not happened")
    return (EscrowState.RECORDED,
            f"rehearsed {d.rehearsed_at.date().isoformat()} by {d.decided_by}, "
            f"{len(d.holders)} holder(s), next drill due "
            f"{d.next_rehearsal_due.date().isoformat()}")


def escrow_survey(keyring: Keyring, *, at: datetime,
                  ) -> Tuple[Tuple[str, EscrowState, str], ...]:
    """Every master this keyring depends on, and what is known about recovering it.

    Derived from the wrappings rather than from a list somebody maintains: a
    master that nothing is wrapped under is not this store's problem, and a
    master that is wrapped under and appears in no escrow record is exactly the
    row this function exists to surface.
    """
    return tuple((m,) + escrow_state(keyring, master_key_id=m, at=at)
                 for m in keyring.masters())
