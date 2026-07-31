"""D-2 acceptance: the drop as a local, ephemeral store (`docs/PLAN-DROP.md` D-2).

Rule 19. D-2's forbidden act is a handle bound to mailbox A requesting mailbox
B's contents, and the refusal is **structural** — B's contents are
unrepresentable from A's handle (`scout-03` acceptance test 1). The second axis
is fail-closed: the drop refuses to operate without its key material.

Stdlib and `drop/`. Runs under pytest or directly:

    python3 -m pytest tests/test_drop_store.py -q
    python3 tests/test_drop_store.py
"""

from __future__ import annotations

import inspect
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from drop.store import Drop, DropUnavailable, Handle, OwnerCredential  # noqa: E402

A = OwnerCredential("mailbox-a", b"secret-material-for-a")
B = OwnerCredential("mailbox-b", b"secret-material-for-b")


def enrolled() -> Drop:
    d = Drop()
    d.register(A)
    d.register(B)
    return d


# --- hold, hand over, delete ------------------------------------------------


def test_deposit_hold_handover_delete():
    d = enrolled()
    d.deposit("mailbox-a", b"opaque-ciphertext-1")
    d.deposit("mailbox-a", b"opaque-ciphertext-2")
    handle = d.owner(A)
    assert handle.collect() == (b"opaque-ciphertext-1", b"opaque-ciphertext-2")
    handle.delete()
    assert handle.collect() == (), "delete did not clear the mailbox"


# --- forbidden act: a handle for A cannot reach B ---------------------------


def test_a_handle_names_no_mailbox_id_structurally():
    """The un-passable-parameter discipline (deliver()'s missing `to`). collect()
    and delete() take no argument, so a handle for A has no way to *express* a
    request for B — unrepresentable, not rejected after a check."""
    for method in (Handle.collect, Handle.delete):
        params = set(inspect.signature(method).parameters) - {"self"}
        assert params == set(), (
            f"Handle.{method.__name__} grew a parameter {sorted(params)} — a "
            "mailbox a session can name is a mailbox it can enumerate")


def test_a_handle_for_a_cannot_read_b():
    """The structural isolation, behaviourally. A payload deposited to A is held
    under a slot derived from A's secret material; B's handle collects under B's
    slot and cannot form A's, so it sees nothing of A's."""
    d = enrolled()
    d.deposit("mailbox-a", b"a-only-ciphertext")
    assert d.owner(B).collect() == (), (
        "a handle bound to B read A's contents — mailboxes are not isolated")
    assert d.owner(A).collect() == (b"a-only-ciphertext",)


# --- forbidden act: a forged or keyless credential --------------------------


def test_a_forged_credential_is_refused():
    """Authentication is fail-closed: the material presented must match the one
    the mailbox is registered under. A forged credential (right id, wrong
    material) gets no handle."""
    d = enrolled()
    forged = OwnerCredential("mailbox-a", b"not-a's-material")
    try:
        d.owner(forged)
    except DropUnavailable:
        return
    raise AssertionError("a forged credential was handed a live handle")


def test_a_credential_with_no_material_is_not_a_credential():
    """Fail-closed, the drop half (acceptance test 2). A credential with no key
    material is refused at construction — the drop never binds a mailbox it
    cannot authenticate."""
    try:
        OwnerCredential("mailbox-a", b"")
    except DropUnavailable:
        return
    raise AssertionError("a credential with no key material was constructible")


def test_an_unregistered_mailbox_gets_no_handle():
    d = enrolled()
    stranger = OwnerCredential("mailbox-z", b"stranger-material")
    try:
        d.owner(stranger)
    except DropUnavailable:
        return
    raise AssertionError("the drop bound a mailbox it never registered")


def test_a_deposit_to_an_unregistered_mailbox_is_refused():
    d = enrolled()
    try:
        d.deposit("mailbox-z", b"nowhere-to-hold-this")
    except DropUnavailable:
        return
    raise AssertionError("a deposit was held for a mailbox no session can form")


def test_a_re_registration_that_changes_the_owner_is_refused():
    d = enrolled()
    try:
        d.register(OwnerCredential("mailbox-a", b"a-new-owners-material"))
    except DropUnavailable:
        return
    raise AssertionError("a mailbox was taken over by a re-registration")


# --- the store holds no schema and no byte at rest --------------------------


def test_the_drop_holds_opaque_bytes_only():
    d = enrolled()
    try:
        d.deposit("mailbox-a", "a string, not bytes")  # type: ignore[arg-type]
    except TypeError:
        pass
    else:
        raise AssertionError("the drop accepted a typed payload it could read")
    try:
        d.deposit("mailbox-a", b"")
    except ValueError:
        return
    raise AssertionError("the drop held an empty deposit as though a mailbox was written to")


# --- negative control -------------------------------------------------------


def test_the_drop_is_not_broken_shut():
    d = enrolled()
    d.deposit("mailbox-b", b"b-ciphertext")
    assert d.owner(B).collect() == (b"b-ciphertext",)


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"ok   {name}")
            except Exception as exc:
                failures += 1
                print(f"FAIL {name}\n{type(exc).__name__}: {exc}\n")
    raise SystemExit(1 if failures else 0)
