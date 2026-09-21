"""Guardian receipts: the only witness whose interest is adverse to the institution's.

§18 item 15 asks who witnesses the anchor. Every external candidate — a
timestamp authority, a public chain, certified mail — is a *neutral* party. This
one is not neutral, and that is the point: **a guardian's interest is
structurally opposed to the institution's**, and a receipt in a parent's hands
cannot be collected back.

**What a receipt is.** When something is written into a student's lane, every
guardian with live standing gets a small artifact naming the lane, the position
in that lane's chain, the entry digest and the time. They keep it. Nothing
about the entry's *content* travels — the digest is opaque, and the receipt is
about the fact of a record existing.

**What makes it strong, and it is stronger than a neutral witness in one way.**
Positions are per-lane (`Ledger`, §5's partitioning), so a position means *"the
nth thing about your child"*. A guardian holding receipts for positions 1, 2, 3
and 5 can see that **4 is missing** — without the institution's cooperation,
without a third party, and without knowing anything about any other student.
Sequence gaps are detectable *by the counterparty*, which is not true of any
anchor.

**What makes it weak, and it is fatal on its own.** An entry the institution
never wrote produces no receipt, and its absence is invisible: a guardian
holding 1..N cannot tell whether N is everything. Receipts detect *removal*,
never *omission*. They corroborate; they do not stand alone.

**On authenticity, and this is the part §18 item 15 carries as a dependency.**
Issuance is tagged by a `Signer`, and there are two kinds it can be:

* **attributable** — an asymmetric signature, which a third party can check
  against a public key without being able to produce one. This is what a
  deployment wants and **this repository does not ship it**: the stdlib carries
  no asymmetric primitive, vendoring curve arithmetic into a records module
  would be the worst version of §16's copied pair, and adding a dependency is a
  maintainer's decision rather than a module's. `Issuance.ATTRIBUTABLE` and the
  `Signer` protocol are the socket it plugs into.
* **self-verifiable** — the HMAC tag `HmacTagger` produces. The institution can
  check its own receipts, so a mismatch between a held receipt and the log is a
  contradiction it must explain. Anyone holding the key can mint one, so a third
  party cannot attribute. That weaker property is **named in every receipt**
  rather than left in this docstring, and `receipt_text()` prints it in words on
  the artifact a guardian keeps.

**The absence is a state, not a default.** A deployment that asks for the
asymmetric path and does not have it gets `AsymmetricUnavailable`, whose `tag()`
raises: it does not quietly hand back an HMAC that looks the same at the call
site. Rule 13, applied to a primitive rather than to a lookup.

Stdlib only. No network.
"""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Protocol, Sequence, Tuple, Union

from .disclosure import Entry, Ledger, Log
from .export import Artifact
from .serving import Edge


class Issuance(Enum):
    """What a receipt's tag is worth against someone who did not issue it."""

    ATTRIBUTABLE = "attributable"          # a third party can attribute it
    SELF_VERIFIABLE = "self_verifiable"    # the issuer can check its own
    UNAVAILABLE = "unavailable"            # asked for, and not present

    @property
    def limit(self) -> str:
        """The sentence that goes on the artifact. Written for the holder."""
        return {
            Issuance.ATTRIBUTABLE: (
                "Anyone can check this receipt came from the programme, without "
                "the programme's help and without being able to produce one."),
            Issuance.SELF_VERIFIABLE: (
                "The programme can check this receipt is one it issued. Someone "
                "else cannot: anyone holding the programme's key could produce a "
                "receipt like this one. What makes it worth keeping is that you "
                "hold it and the programme cannot take it back."),
            Issuance.UNAVAILABLE: (
                "No means of checking this receipt is available. That is a "
                "problem to report, not a receipt to rely on."),
        }[self]


class NoSigner(RuntimeError):
    """The issuance scheme this deployment asked for is not present."""


class Uncheckable(ValueError):
    """Asked to verify a receipt with something that cannot read its scheme.

    Raised rather than answered `False`, because *this is forged* and *I cannot
    check this* are different facts and a boolean makes them identical — which
    is rule 13 arriving at a verifier.
    """


class Signer(Protocol):
    """The issuance seam. An asymmetric implementation plugs in here."""

    scheme: str
    issuance: Issuance

    def tag(self, material: str) -> str: ...
    def verify(self, material: str, tag: str) -> bool: ...


@dataclass(frozen=True)
class HmacTagger:
    """The fallback, in the stdlib, saying what it is."""

    key: bytes
    scheme: str = "hmac-sha256"
    issuance: Issuance = Issuance.SELF_VERIFIABLE

    def tag(self, material: str) -> str:
        return f"{self.scheme}:" + hmac.new(
            self.key, material.encode("utf-8"), hashlib.sha256).hexdigest()

    def verify(self, material: str, tag: str) -> bool:
        return hmac.compare_digest(tag, self.tag(material))


@dataclass(frozen=True)
class AsymmetricUnavailable:
    """What a deployment gets when it asks for a primitive the box lacks.

    It refuses rather than substituting. A silent fall back to HMAC would make
    *attributable* and *self-verifiable* look identical at every call site, and
    the first place anyone would notice is a dispute.
    """

    scheme: str = "ed25519"
    issuance: Issuance = Issuance.UNAVAILABLE

    def tag(self, material: str) -> str:
        raise NoSigner(
            f"{self.scheme} issuance was asked for and no primitive is available. "
            "Receipts are not issued unsigned, and are not quietly issued under a "
            "weaker scheme; wire a signer or issue self-verifiable receipts "
            "deliberately")

    def verify(self, material: str, tag: str) -> bool:
        raise NoSigner(
            f"{self.scheme} verification was asked for and no primitive is "
            "available; this is unknown, not a mismatch")


def _ed25519_primitives():
    """The one import of this repository's one dependency (§18 item 15,
    decided 2026-07-31). Lazy, so a box missing it still imports `records` —
    and then *refuses* attributable issuance rather than downgrading, which is
    `AsymmetricUnavailable`'s whole job."""
    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives.asymmetric.ed25519 import (
            Ed25519PrivateKey, Ed25519PublicKey)
    except BaseException as exc:  # noqa: BLE001 — deliberate, and narrow in effect:
        # an *absent* install raises ImportError, but a *broken* one (a wheel
        # built for another interpreter) raises whatever its bindings panic
        # with — observed 2026-07-31 as a pyo3 PanicException, which is neither
        # ImportError nor even Exception. Both are the same fact at this seam:
        # the primitive is not available, and the refusal must say so with the
        # cause attached rather than let an unnamed crash speak for it.
        raise NoSigner(
            "ed25519 issuance is decided and its primitive is not usable on "
            "this box; the dependency is declared in requirements.txt, so this "
            "is a broken or absent install, not a reason to fall back"
        ) from exc
    return Ed25519PrivateKey, Ed25519PublicKey, InvalidSignature


@dataclass(frozen=True)
class Ed25519Signer:
    """The attributable path — wired 2026-07-31, when the maintainer accepted
    the repository's first dependency for it (§18 item 15).

    Carries the raw public key always and the private seed only on the issuing
    side, so the object a third party holds *cannot* mint: `tag()` without the
    seed raises `NoSigner` rather than quietly signing with nothing. What
    attribution buys over `HmacTagger` is exactly that asymmetry — anyone can
    check a receipt came from the programme; only the programme can produce one.
    """

    public_key: bytes                       # 32 raw bytes; every holder has this
    private_seed: Optional[bytes] = None    # 32 raw bytes; the issuer alone
    scheme: str = "ed25519"
    issuance: Issuance = Issuance.ATTRIBUTABLE

    def tag(self, material: str) -> str:
        Priv, _, _ = _ed25519_primitives()
        if self.private_seed is None:
            raise NoSigner(
                "this signer holds the public key only; it can verify and "
                "cannot issue — which is the property that makes the receipt "
                "worth holding")
        sig = Priv.from_private_bytes(self.private_seed).sign(
            material.encode("utf-8"))
        return f"{self.scheme}:{sig.hex()}"

    def verify(self, material: str, tag: str) -> bool:
        _, Pub, InvalidSignature = _ed25519_primitives()
        prefix = f"{self.scheme}:"
        if not tag.startswith(prefix):
            raise Uncheckable(
                f"this verifier reads {self.scheme} tags and was handed one it "
                "cannot parse; that is unknown, not a mismatch")
        try:
            raw = bytes.fromhex(tag[len(prefix):])
        except ValueError:
            raise Uncheckable(
                f"a {self.scheme} tag that does not decode is unreadable, "
                "not forged") from None
        try:
            Pub.from_public_bytes(self.public_key).verify(
                raw, material.encode("utf-8"))
        except InvalidSignature:
            return False
        return True


def generate_signer() -> Ed25519Signer:
    """A fresh issuing signer. The seed's custody is the deployment's problem
    (§5's vault); nothing here persists anything."""
    Priv, _, _ = _ed25519_primitives()
    from cryptography.hazmat.primitives import serialization
    key = Priv.generate()
    seed = key.private_bytes(
        serialization.Encoding.Raw, serialization.PrivateFormat.Raw,
        serialization.NoEncryption())
    pub = key.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return Ed25519Signer(public_key=pub, private_seed=seed)


def schemes() -> Tuple[str, ...]:
    """Issuance schemes this tree can actually perform, derived from itself.

    Read by `tools/conform.py`. Derived by *attempting the import*, never by
    assuming the requirements file was honoured — a box where the install
    broke reports hmac-only, and `receipt-attribution` stops passing there,
    which is the point of deriving it.
    """
    try:
        _ed25519_primitives()
    except NoSigner:
        return (HmacTagger(b"").scheme,)
    return (Ed25519Signer(b"\x00" * 32).scheme, HmacTagger(b"").scheme)


def _as_signer(verifier: Union[bytes, "Signer"]) -> "Signer":
    return HmacTagger(verifier) if isinstance(verifier, (bytes, bytearray)) else verifier


@dataclass(frozen=True)
class GuardianReceipt:
    """What a guardian keeps. Opaque about content, precise about existence.

    `issuance` is the seventh field and it is not decoration: a receipt that
    does not say what its own tag is worth is a receipt whose holder will assume
    the stronger reading. It is covered by the tag, so it cannot be relabelled
    after issue.
    """

    lane_id: str
    position: int          # 1-based, within this lane only
    entry_digest: str
    issued_at: datetime
    to_guardian: str
    tag: str               # scheme-prefixed; see the module note
    issuance: Issuance = Issuance.SELF_VERIFIABLE

    def matches(self, entry: Entry) -> bool:
        return entry.digest == self.entry_digest

    @property
    def scheme(self) -> str:
        """The scheme named on the tag itself, so a holder with no key can read
        what kind of thing they have."""
        return self.tag.split(":", 1)[0] if ":" in self.tag else "unnamed"


def _material(lane_id: str, position: int, digest: str, issued_at: datetime,
              to_guardian: str, issuance: Issuance) -> str:
    return "\x1f".join([lane_id, str(position), digest, issued_at.isoformat(),
                        to_guardian, issuance.value])


def issue(ledger: Ledger, lane_id: str, subject_id: str, edges: Sequence[Edge],
          at: datetime, key: Optional[bytes] = None, *,
          signer: Optional["Signer"] = None) -> Tuple[GuardianReceipt, ...]:
    """Receipts for the newest entry in `lane_id`, to guardians with standing.

    **Standing, not reachability.** A guardian under a contact restriction may
    not be *messaged* (`records/sending.py`), and that is a question about
    delivery. Whether they still hold records standing is a different question
    with a different answer, and conflating them here would let a contact
    restriction quietly revoke someone's ability to audit their own child's
    record. Delivery is the caller's problem; this decides who is owed one.

    Takes a key or a signer, never both, so that *which scheme issued this* is
    always a thing somebody chose.
    """
    if (key is None) == (signer is None):
        raise ValueError(
            "issue() takes a key or a signer and not both; the issuance scheme "
            "is recorded on every receipt and must not be arrived at by default")
    tagger = _as_signer(key if key is not None else signer)
    log = ledger.log_for(lane_id)
    if not log.entries:
        return ()
    position = len(log.entries)
    entry = log.entries[-1]
    out = []
    for e in edges:
        if e.kind != "guardian_of" or e.subject_id != subject_id:
            continue
        if not e.live_at(at):
            continue
        material = _material(lane_id, position, entry.digest, at,
                             e.principal_id, tagger.issuance)
        out.append(GuardianReceipt(
            lane_id, position, entry.digest, at, e.principal_id,
            tagger.tag(material), tagger.issuance))
    return tuple(out)


def authentic(receipt: GuardianReceipt, verifier: Union[bytes, "Signer"]) -> bool:
    """Whether this receipt carries a tag this issuer would have produced.

    Raises `Uncheckable` when the verifier cannot read the receipt's scheme.
    Returning `False` there would report an Ed25519 receipt checked with an HMAC
    key as *not authentic*, which is the strongest possible way to say *I did
    not look*.
    """
    v = _as_signer(verifier)
    if v.issuance is not receipt.issuance or receipt.scheme != v.scheme:
        raise Uncheckable(
            f"this receipt was issued {receipt.issuance.value} under "
            f"{receipt.scheme}; the verifier offered is {v.issuance.value} under "
            f"{v.scheme}. That is unknown, not a mismatch")
    return v.verify(_material(receipt.lane_id, receipt.position,
                              receipt.entry_digest, receipt.issued_at,
                              receipt.to_guardian, receipt.issuance),
                    receipt.tag)


def receipt_text(receipt: GuardianReceipt) -> Artifact:
    """The receipt as a page, with its own limit printed on it.

    A holder who is told nothing assumes the strongest reading, so the weaker
    property travels with the artifact rather than living in a docstring. The
    caller writes it; nothing here touches a filesystem (§6).
    """
    lines = [
        "RECEIPT FOR A RECORD ABOUT YOUR CHILD",
        "=====================================",
        "",
        f"issued to    {receipt.to_guardian}",
        f"issued       {receipt.issued_at.isoformat()}",
        f"this is      record number {receipt.position} in your child's file",
        "",
        "WHAT THIS IS",
        "------------",
        "The programme wrote something into your child's record. This slip says",
        "so. It does not say what was written — the code below is not readable",
        "and cannot be turned back into words.",
        "",
        f"  {receipt.entry_digest}",
        "",
        "WHY THE NUMBER MATTERS",
        "----------------------",
        "The number counts only records about your child. If you hold slips 1,",
        "2, 3 and 5, then record 4 existed and is gone, and you can show that",
        "without anyone's help. Keep them.",
        "",
        "WHAT THIS SLIP CANNOT TELL YOU",
        "------------------------------",
        "Whether anything was left out. A record never written leaves no slip,",
        "so holding every slip up to 5 does not prove there were only five.",
        "",
        "HOW FAR THIS CAN BE CHECKED",
        "---------------------------",
        f"  scheme: {receipt.scheme}",
        f"  {receipt.issuance.limit}",
        "",
    ]
    return Artifact(f"receipt-{receipt.lane_id}-{receipt.position}.txt",
                    "text/plain", "\n".join(lines))


def held_by(receipts: Sequence[GuardianReceipt], guardian_id: str,
            lane_id: Optional[str] = None) -> Tuple[GuardianReceipt, ...]:
    return tuple(sorted(
        (r for r in receipts
         if r.to_guardian == guardian_id and (lane_id is None or r.lane_id == lane_id)),
        key=lambda r: r.position))


def gaps(receipts: Sequence[GuardianReceipt]) -> Tuple[int, ...]:
    """Positions missing from a guardian's own sequence.

    **The property no anchor gives.** Holding 1, 2, 3, 5 proves 4 existed and
    is gone, without the institution's cooperation and without learning
    anything about any other student. Detectable by the counterparty, which is
    what makes an adverse witness worth having.

    Requires the receipts to be for one lane and one guardian; mixing either
    would compare sequences that are not sequences.
    """
    if not receipts:
        return ()
    lanes = {r.lane_id for r in receipts}
    holders = {r.to_guardian for r in receipts}
    if len(lanes) > 1 or len(holders) > 1:
        raise ValueError(
            "gaps() needs one lane and one guardian; positions are per-lane and "
            "a mixed sequence has no meaningful holes"
        )
    seen = {r.position for r in receipts}
    return tuple(p for p in range(1, max(seen) + 1) if p not in seen)


def contradictions(log: Log, receipts: Sequence[GuardianReceipt]) -> Tuple[str, ...]:
    """Where a guardian's held receipts disagree with the institution's log.

    Three shapes, and the first is the one that matters: a receipt for a
    position the log no longer reaches means an entry was removed after it was
    receipted.
    """
    out = []
    for r in sorted(receipts, key=lambda r: r.position):
        if r.position > len(log.entries):
            out.append(f"position {r.position} was receipted and the log now ends at "
                       f"{len(log.entries)}")
            continue
        entry = log.entries[r.position - 1]
        if not r.matches(entry):
            out.append(f"position {r.position} holds a different entry than the "
                       "receipt issued for it")
    return tuple(out)
