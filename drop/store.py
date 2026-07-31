"""D-2 — the drop, as a local, ephemeral store: hold, hand over, delete.

`docs/PLAN-DROP.md` D-2, the `briar-mailbox` shape reimplemented rather than
vendored (§16; `scout-03` §1). Its whole job (§3, *The drop*): authenticate a
connection as belonging to a mailbox, accept opaque ciphertext addressed to a
mailbox, hold it, hand it over, delete it. No schema of the domain — the payload
is opaque bytes, not a queryable record — no listener, no socket.

**Non-enumerability is structural, not checked (D-2's forbidden act).** A handle
is bound to exactly one mailbox and there is no method on it that takes a mailbox
id: *"which mailbox?"* is never a parameter a caller supplies, which is the
un-passable-parameter discipline `records/sending.py::deliver` applies to a
recipient, carried to the relay's own API. And it is structural under the hood
too: what a mailbox holds is keyed by a **slot derived from the owner's secret
material** (`_slot`), never by the mailbox name. A handle for mailbox A cannot
form mailbox B's slot, because forming it needs B's material, which A's handle
does not have. B's contents are unrepresentable from A's handle rather than
rejected after a check (`scout-03` acceptance test 1). The registration table of
opaque ids and their material is the drop's alone — §3 permits *"opaque mailbox
identifiers and their public keys"* — and it is what a **session** can never
enumerate.

**Fail-closed, the `jeles-remote` bar (§4.3).** A credential with no key material
is not a credential (`OwnerCredential.__post_init__`), and the drop refuses to
issue a handle for a mailbox whose material does not match the one registered:
it refuses to operate without its key material and says so, never degrading to
handing out a mailbox it cannot authenticate.

**Ephemeral, on purpose — the R16 decision (`docs/PLAN-DROP.md`, R16 note).** The
hold is a dict in memory, dropped with the process. Nothing here writes a byte
to disk, so a held sealed payload does **not** outlive the process that wrote it
(`tools/audit.py::AT_REST_BOUNDARY`), `durable_callers()` stays empty, and R16
stays `FINDING`/`S2`. This is also §4.3's *"stateless, scales to zero"* and
`chatmail`'s *auto-delete* posture. A **durable** hold — a spool that survives a
restart — would put a sealed payload at rest and is a real, later decision; it is
deferred here with a tombstone rather than smuggled in (see `_DURABLE_HOLD`).

Stdlib and `records/` (only for the exception idiom shape). No network, no store,
no model, no filesystem.
"""

from __future__ import annotations

import hashlib
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


#: **Tombstone (rule 20).** A durable hold — a spool that survives a process
#: restart — is deliberately not built here.
#:
#: * status: deferred, ephemeral hold shipped in its place.
#: * successor: a future ops phase, the same one that builds the hosted relay
#:   (`docs/PLAN-DROP.md`, *Deferred deliberately*). It brings its own dated
#:   escrow rehearsal, because a durable sealed payload IS a byte that outlives
#:   the process (`tools/audit.py::AT_REST_BOUNDARY`) and would move R16 to `S1`
#:   without one.
#: * why the stub is a comment and not a knob: a `durable=True` flag would let a
#:   caller flip the R16-relevant property without the escrow decision that owes
#:   it. The absence of the knob is the enforcement.
_DURABLE_HOLD = (
    "deferred: the hold is ephemeral (in-memory). A durable spool outlives the "
    "process and is an at-rest store (R16 S1 without a rehearsed escrow); it is a "
    "later ops-phase decision, not a flag on this store")


class DropUnavailable(Exception):
    """The drop cannot serve a mailbox, and *why* is the payload of this error.

    Raised rather than degraded, `records/atrest.py::PrimitiveUnavailable`'s
    reason applied to the relay: a drop that handed out a handle it could not
    authenticate, or operated with no key material, would make an owned mailbox
    and a forged one look identical at every call site.
    """


def _slot(material: bytes) -> str:
    """The opaque slot a mailbox's payloads are held under.

    Derived from the owner's **secret material**, never from the mailbox name.
    This is what makes non-enumerability structural: a session holding A's
    material cannot form B's slot, so there is no index over mailboxes for a
    session to walk. The drop process holds the registration and can address a
    deposit; a connected **session** holds only its own material and can address
    only its own slot.
    """
    return hashlib.sha256(b"drop-slot:" + material).hexdigest()


@dataclass(frozen=True)
class OwnerCredential:
    """What binds a session to one mailbox. The credential **is** the binding.

    `mailbox_id` is the opaque name a depositor addresses; `material` is the
    secret that authorizes collection and derives the slot. Possession of the
    material is the authorization, so there is no separate *"which mailbox may I
    read"* parameter anywhere — the material answers it and nothing else can.
    """

    mailbox_id: str
    material: bytes

    def __post_init__(self):
        if not (self.mailbox_id or "").strip():
            raise ValueError("a mailbox with no id cannot be addressed")
        if not self.material:
            raise DropUnavailable(
                "a credential with no key material is not a credential; the drop "
                "fails closed rather than binding a mailbox it cannot authenticate "
                "(fail-closed, §4.3)")

    def __repr__(self) -> str:
        # Material is a secret; a dataclass repr in a traceback is a rendering,
        # and tracebacks reach logs. `records/atrest.py`'s discipline.
        return f"OwnerCredential(mailbox_id={self.mailbox_id!r}, material=<withheld>)"


@dataclass
class Handle:
    """A session bound to exactly one mailbox. **It names no mailbox id.**

    `collect()` and `delete()` take no argument: the mailbox is `_slot`, fixed
    at binding from the owner's material. There is nowhere to put another
    mailbox's id, which is why a handle for A cannot express a request for B —
    the same property `deliver()` gets from having no `to`. `tests/test_drop_store.py`
    asserts that statically over the signatures, as `test_sending.py` does G4.
    """

    _drop: "Drop"
    _slot: str
    mailbox_id: str

    def collect(self) -> Tuple[bytes, ...]:
        """Hand over everything held for **this** mailbox. No id, by construction."""
        return self._drop._held_at(self._slot)

    def delete(self) -> None:
        """Delete what is held for this mailbox. The drop collects nothing else."""
        self._drop._clear(self._slot)


@dataclass
class Drop:
    """The ephemeral local store: registration, deposit, hand-over, delete.

    Holds no domain schema — `_held` is `slot -> [opaque bytes]` — and no user
    table beyond `_registered`, the opaque ids and their material §3 permits. In
    memory only; the process ending is the auto-delete.
    """

    _held: Dict[str, List[bytes]] = field(default_factory=dict)
    _registered: Dict[str, bytes] = field(default_factory=dict)

    def register(self, credential: OwnerCredential) -> None:
        """Enrol a mailbox so deposits can be addressed to it.

        Re-registering with different material is refused: a mailbox whose
        material changed under a live registration is a mailbox somebody is
        trying to take over, and silently accepting it would let a forged
        credential become the registered one.
        """
        known = self._registered.get(credential.mailbox_id)
        if known is not None and known != credential.material:
            raise DropUnavailable(
                f"mailbox {credential.mailbox_id!r} is registered under different "
                "material; a re-registration that changed the owner's key is a "
                "takeover, not an enrolment")
        self._registered[credential.mailbox_id] = credential.material

    def deposit(self, mailbox_id: str, ciphertext: bytes) -> None:
        """Accept opaque ciphertext addressed to a registered mailbox (§3).

        A deposit to a mailbox nobody registered is refused rather than held in a
        slot no session can ever form — a payload the drop could never hand over
        is a leak of *that a deposit was attempted* and nothing else. The bytes
        are opaque; the drop asserts they are bytes and nothing about their shape.
        """
        if not isinstance(ciphertext, (bytes, bytearray)):
            raise TypeError("the drop holds opaque bytes; encoding is the "
                            "producer's decision and the drop reads none of it")
        if not ciphertext:
            raise ValueError("an empty deposit holds nothing; the drop refuses it "
                             "rather than recording that a mailbox was written to")
        material = self._registered.get(mailbox_id)
        if material is None:
            raise DropUnavailable(
                f"mailbox {mailbox_id!r} is not registered; a deposit the drop "
                "could never hand over is refused")
        self._held.setdefault(_slot(material), []).append(bytes(ciphertext))

    def owner(self, credential: OwnerCredential) -> Handle:
        """Bind a session to a mailbox, authenticating the owner.

        **The authentication is the fail-closed guard.** The presented material
        must match what the mailbox is registered under; a mismatch (a forged or
        stale credential) is refused rather than handed a live handle. Belt and
        suspenders over the structural slot keying: even a forged handle would
        collect nothing, but a drop that issues a handle it cannot authenticate
        has already stopped saying no.
        """
        registered = self._registered.get(credential.mailbox_id)
        if registered is None:
            raise DropUnavailable(
                f"mailbox {credential.mailbox_id!r} is not registered; the drop "
                "issues a handle only for a mailbox it knows")
        if registered != credential.material:
            raise DropUnavailable(
                f"the material presented for {credential.mailbox_id!r} does not "
                "match its registration; the drop refuses to bind a mailbox it "
                "cannot authenticate (fail-closed, §4.3)")
        return Handle(self, _slot(credential.material), credential.mailbox_id)

    # --- internals a Handle reaches, and a session cannot ------------------

    def _held_at(self, slot: str) -> Tuple[bytes, ...]:
        """What is held under one slot. Reached only through a bound Handle."""
        return tuple(self._held.get(slot, ()))

    def _clear(self, slot: str) -> None:
        self._held.pop(slot, None)
