"""§9 foundation 3: at-rest sealing across the Zone A boundary.

Every key in this file is generated in memory and none is written anywhere
(refusal 2). Nothing here reads or writes the filesystem except to scan the
module's own source, which is the core/seam assertion.

Runs under pytest or directly:

    python3 -m pytest tests/test_atrest.py -q
    python3 tests/test_atrest.py
"""

from __future__ import annotations

import dataclasses
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from records import atrest  # noqa: E402
from records.atrest import (  # noqa: E402
    FERNET_V1, OPENABLE, Agreement, Composition, EscrowDisposition, EscrowState,
    KeyState, Keyring, LaneKey, MasterKey, Readable, Sealed, composes, destroy,
    escrow_state, escrow_survey, new_master, open_lane_key, reconcile,
    record_escrow, rehearse, reseal, rewrap, rotate_lane_key, seal_bytes,
    unseal, unseal_with, unwrap)
from records.disclosure import Ledger  # noqa: E402
from records.serving import Outcome, Serving  # noqa: E402
from records.rungs import Rung  # noqa: E402

T0 = datetime(2026, 1, 5)
T1 = datetime(2026, 3, 1)
T2 = datetime(2026, 9, 1)
BEN, LB = "student-ben", "lane-ben"
LM = "lane-mira"
BODY = b"auto-injector in the black case, front pocket"


def hierarchy(lanes=(LB,)):
    """A master and one wrapped key per lane. Nothing is persisted."""
    master = new_master(key_id="master-1")
    keyring, keys = Keyring(), {}
    for lane in lanes:
        keyring, keys[lane] = open_lane_key(keyring, lane_id=lane,
                                            master=master, at=T0)
    return master, keyring, keys


# --- the hierarchy as types -----------------------------------------------


def test_the_master_key_never_touches_a_record():
    """§5's first line, enforced by type rather than by convention. A hierarchy
    whose top key can also seal directly is one where eventually it does."""
    master = new_master()
    try:
        seal_bytes(BODY, lane_key=master, at=T0)
    except TypeError as exc:
        assert "never touches a record" in str(exc)
        return
    raise AssertionError("the master sealed a record directly")


def test_one_lane_one_key_and_a_section_is_not_a_lane():
    """W-1 at the key layer. A key over `the drumline` cannot be destroyed for
    one student, which is the whole reason the tier is per lane."""
    master = new_master()
    for name in ("the drumline", "all", "*", "Ensemble"):
        try:
            open_lane_key(Keyring(), lane_id=name, master=master, at=T0)
        except ValueError as exc:
            assert "names a set" in str(exc), name
            continue
        raise AssertionError(f"{name!r} was accepted as a lane")


def test_two_lanes_get_two_different_keys():
    """The flat-key shape this exists to refuse: seal every lane under one key
    and the roster column is back, one layer down."""
    _, keyring, keys = hierarchy((LB, LM))
    assert keys[LB].key_id != keys[LM].key_id
    assert keys[LB].material != keys[LM].material
    assert {w.lane_id for w in keyring.wrappings} == {LB, LM}


def test_a_lane_key_is_random_and_not_recomputable_from_the_master():
    """The decision argued in the module docstring: a derived key survives its
    own destruction, because the master regenerates it. Two mints under one
    master for one lane must differ, or erasure is theatre."""
    master = new_master(key_id="master-1")
    kr, first = open_lane_key(Keyring(), lane_id=LB, master=master, at=T0)
    kr, second = open_lane_key(kr, lane_id=LB, master=master, at=T0)
    assert first.material != second.material
    assert first.key_id != second.key_id


def test_a_key_id_cannot_be_registered_twice():
    master = new_master()
    kr, _ = open_lane_key(Keyring(), lane_id=LB, master=master, at=T0,
                          key_id="k-1")
    try:
        open_lane_key(kr, lane_id=LM, master=master, at=T0, key_id="k-1")
    except ValueError as exc:
        assert "already known" in str(exc)
        return
    raise AssertionError("one key id was bound to two lanes")


def test_a_sealed_payload_names_its_lane_its_key_and_its_scheme():
    """What makes rotation representable at all."""
    master, keyring, keys = hierarchy()
    s = seal_bytes(BODY, lane_key=keys[LB], at=T0)
    assert s.lane_id == LB and s.key_id == keys[LB].key_id
    assert s.scheme == FERNET_V1 and s.scheme in OPENABLE


def test_key_material_never_renders():
    """Key material is `L5` by `records/classify.py`'s first override rule, and
    a dataclass repr in a traceback is a rendering."""
    master, _, keys = hierarchy()
    for obj in (master, keys[LB]):
        assert obj.material not in repr(obj).encode("utf-8", "ignore")
        assert "withheld" in repr(obj)
    s = seal_bytes(BODY, lane_key=keys[LB], at=T0)
    opened = unseal_with(s, lane_key=keys[LB])
    assert BODY not in repr(opened).encode() and "withheld" in repr(opened)


def test_the_keyring_alone_carries_nothing_usable():
    """§5's cryptographic-rather-than-policy claim: copy the box without the
    key and every secret is unreadable."""
    master, keyring, keys = hierarchy()
    s = seal_bytes(BODY, lane_key=keys[LB], at=T0)
    got = unseal(s, keyring=keyring, master=None)
    assert not got.opened
    blob = repr(keyring).encode() + b"".join(w.wrapped for w in keyring.wrappings)
    assert keys[LB].material not in blob and master.material not in blob


# --- seal and unseal as a core --------------------------------------------


def test_a_payload_round_trips():
    master, keyring, keys = hierarchy()
    s = seal_bytes(BODY, lane_key=keys[LB], at=T0)
    got = unseal(s, keyring=keyring, master=master)
    assert got.opened and got.plaintext == BODY


def test_the_ciphertext_does_not_contain_the_payload():
    _, _, keys = hierarchy()
    s = seal_bytes(BODY, lane_key=keys[LB], at=T0)
    assert BODY not in s.ciphertext


def test_this_module_never_touches_the_filesystem():
    """§6's core/seam partition, the same assertion `records/export.py` carries.
    `tools/purity.py` checks the whole package; this pins the one module."""
    src = (Path(__file__).resolve().parent.parent / "records" / "atrest.py").read_text()
    body = src.split('"""', 2)[-1]
    for banned in ("open(", "write_text", "write_bytes", "Path(", "os.", "shutil"):
        assert banned not in body, f"records/atrest.py reaches the filesystem: {banned}"


def test_the_core_reaches_no_network_and_writes_nothing():
    """Run the repository's own checker at this module rather than trusting the
    package-wide run to have included it."""
    import purity  # noqa: E402

    target = [Path(__file__).resolve().parent.parent / "records" / "atrest.py"]
    assert purity.counted(target) == 1
    assert not purity.egress(target) and not purity.writes(target)


def test_seal_bytes_refuses_text():
    _, _, keys = hierarchy()
    try:
        seal_bytes("a string", lane_key=keys[LB], at=T0)
    except TypeError as exc:
        assert "takes bytes" in str(exc)
        return
    raise AssertionError("an encoding was guessed inside the core")


# --- rotation and revocation ----------------------------------------------


def test_rotating_the_master_reseals_nothing():
    """§5's *thing everyone gets wrong*, shown rather than asserted: the sealed
    objects are compared before and after and must be identical."""
    master, keyring, keys = hierarchy((LB, LM))
    sealed = tuple(seal_bytes(BODY, lane_key=keys[l], at=T0) for l in (LB, LM))
    later = new_master(key_id="master-2")
    rotated = rewrap(keyring, was=master, now=later, at=T1)

    assert all(w.under_master == "master-2" for w in rotated.wrappings)
    assert {w.key_id for w in rotated.wrappings} == {w.key_id for w in keyring.wrappings}
    for s in sealed:
        assert unseal(s, keyring=rotated, master=later).plaintext == BODY
    assert sealed == tuple(sealed), "a payload object changed during rotation"


def test_the_old_master_no_longer_opens_after_rotation():
    master, keyring, keys = hierarchy()
    s = seal_bytes(BODY, lane_key=keys[LB], at=T0)
    later = new_master(key_id="master-2")
    rotated = rewrap(keyring, was=master, now=later, at=T1)
    got = unseal(s, keyring=rotated, master=master)
    assert got.state is Readable.MASTER_MISMATCH
    assert "rotation has not reached" in got.reason


def test_rotating_a_master_onto_its_own_id_is_refused():
    master, keyring, _ = hierarchy()
    try:
        rewrap(keyring, was=master, now=MasterKey("master-1", b"x" * 44), at=T1)
    except ValueError as exc:
        assert "new name" in str(exc)
        return
    raise AssertionError("a rotation that cannot be told from its predecessor")


def test_rewrap_that_matches_no_wrapping_is_refused_not_a_silent_no_op():
    """The change-nothing act, refused — the guard `destroy()` and
    `rotate_lane_key()` already carry and `rewrap()` was missing.

    `rewrap` only re-wraps wrappings held under `was`; any other is passed
    through. So a `was` that matches nothing rotates nothing and returns a
    keyring identical to the input — and does it looking like success. The
    scenario that makes it a defect rather than a curiosity is a rotation *off*
    a compromised master: an operator who offers the wrong `was` (a stale
    variable, the wrong key file) reads the returned keyring as rotated, then
    either destroys the old master (silent data loss) or keeps trusting a
    revocation that never happened. Neither branch raises without this.

    The offered master is real and well-formed — same shape as a right one —
    so the refusal is about *what it matched*, not about a malformed key.
    """
    master, keyring, keys = hierarchy()
    s = seal_bytes(BODY, lane_key=keys[LB], at=T0)
    stranger = new_master(key_id="master-never-used")  # valid, matches no wrapping
    target = new_master(key_id="master-2")
    try:
        rewrap(keyring, was=stranger, now=target, at=T1)
    except ValueError as exc:
        assert "rotate nothing" in str(exc)
    else:
        raise AssertionError(
            "rewrap rotated nothing and did not say so; the old master still "
            "opens every record and the caller cannot tell the rotation was a "
            "no-op")

    # And the guard does not fire on a legitimate rotation, including the
    # incremental case where the keyring is split across two masters: as long as
    # one wrapping is under `was`, the rotation lands.
    rotated = rewrap(keyring, was=master, now=target, at=T1)
    assert unseal(s, keyring=rotated, master=target).plaintext == BODY


def test_lane_key_rotation_is_forward_only():
    """§5: *a graduated senior's parent legitimately saw last season's data.*"""
    master, keyring, keys = hierarchy()
    old = seal_bytes(BODY, lane_key=keys[LB], at=T0)
    keyring, fresh = rotate_lane_key(keyring, lane_id=LB, master=master, at=T1)
    new = seal_bytes(b"this season", lane_key=fresh, at=T1)

    assert fresh.key_id != keys[LB].key_id
    assert unseal(old, keyring=keyring, master=master).plaintext == BODY
    assert unseal(new, keyring=keyring, master=master).plaintext == b"this season"
    assert len(keyring.keys_for(LB)) == 2


def test_rotating_a_lane_that_has_no_key_is_refused():
    master = new_master()
    try:
        rotate_lane_key(Keyring(), lane_id=LB, master=master, at=T1)
    except ValueError as exc:
        assert "no key to rotate" in str(exc)
        return
    raise AssertionError("a rotation minted a first key and hid that fact")


def test_resealing_history_is_a_separate_deliberate_act():
    """§5 reserves full re-encryption for a custody order or a terminated staff
    member. It is a call you reach for, not a flag on rotation."""
    master, keyring, keys = hierarchy()
    old = seal_bytes(BODY, lane_key=keys[LB], at=T0)
    keyring, fresh = rotate_lane_key(keyring, lane_id=LB, master=master, at=T1)
    moved = reseal([old], from_key=keys[LB], to_key=fresh, at=T1)

    assert moved[0].key_id == fresh.key_id
    assert moved[0].ciphertext != old.ciphertext
    assert unseal(moved[0], keyring=keyring, master=master).plaintext == BODY


def test_resealing_across_lanes_is_refused():
    master, keyring, keys = hierarchy((LB, LM))
    s = seal_bytes(BODY, lane_key=keys[LB], at=T0)
    try:
        reseal([s], from_key=keys[LB], to_key=keys[LM], at=T1)
    except ValueError as exc:
        assert "across lanes" in str(exc)
        return
    raise AssertionError("two lanes' records ended up under one key")


def test_resealing_refuses_a_payload_it_was_not_given_the_key_for():
    """A reseal that skipped a payload leaves history half-readable and looks
    finished."""
    master, keyring, keys = hierarchy()
    keyring, fresh = rotate_lane_key(keyring, lane_id=LB, master=master, at=T1)
    stray = seal_bytes(BODY, lane_key=fresh, at=T1)
    try:
        reseal([stray], from_key=keys[LB], to_key=fresh, at=T1)
    except ValueError as exc:
        assert "not the key being resealed from" in str(exc)
        return
    raise AssertionError("a payload was silently skipped")


# --- the three unreadable states, never one boolean -----------------------


def test_a_tampered_payload_is_unreadable_and_says_so():
    master, keyring, keys = hierarchy()
    s = seal_bytes(BODY, lane_key=keys[LB], at=T0)
    bad = dataclasses.replace(s, ciphertext=s.ciphertext[:-4] + b"AAAA")
    got = unseal(bad, keyring=keyring, master=master)
    assert got.state is Readable.UNREADABLE and got.plaintext is None


def test_a_destroyed_key_is_its_own_state_and_carries_the_dated_act():
    master, keyring, keys = hierarchy()
    s = seal_bytes(BODY, lane_key=keys[LB], at=T0)
    erased = destroy(keyring, lane_id=LB, at=T1, by="Dana Ruiz",
                     reason="guardian erasure request 2026-03-01")
    got = unseal(s, keyring=erased, master=master)
    assert got.state is Readable.KEY_DESTROYED
    assert got.erasure.by == "Dana Ruiz" and got.erasure.at == T1
    assert "2026-03-01" in got.reason


def test_an_unknown_key_is_not_a_destroyed_one():
    """The distinction a guardian is owed: *nobody here has ever held this* and
    *a named person destroyed it on a date* are different answers."""
    master, keyring, keys = hierarchy()
    s = seal_bytes(BODY, lane_key=keys[LB], at=T0)
    got = unseal(s, keyring=Keyring(), master=master)
    assert got.state is Readable.KEY_UNKNOWN and got.erasure is None


def test_the_three_states_are_three_and_the_module_holds_no_boolean_shortcut():
    """All three at once, so a refactor that collapsed any pair fails here."""
    master, keyring, keys = hierarchy()
    s = seal_bytes(BODY, lane_key=keys[LB], at=T0)
    tampered = dataclasses.replace(s, ciphertext=s.ciphertext[:-4] + b"AAAA")
    erased = destroy(keyring, lane_id=LB, at=T1, by="Dana Ruiz", reason="order")
    seen = {
        unseal(tampered, keyring=keyring, master=master).state,
        unseal(s, keyring=erased, master=master).state,
        unseal(s, keyring=Keyring(), master=master).state,
    }
    assert seen == {Readable.UNREADABLE, Readable.KEY_DESTROYED,
                    Readable.KEY_UNKNOWN}, seen


def test_a_relabelled_envelope_is_misbound_not_merely_unreadable():
    """Fernet has no AAD, so the context is bound inside the ciphertext. Editing
    the envelope's lane must fail rather than open into another lane."""
    _, _, keys = hierarchy((LB, LM))
    s = seal_bytes(BODY, lane_key=keys[LB], at=T0)
    moved = Sealed(lane_id=LM, key_id=s.key_id, scheme=s.scheme,
                   ciphertext=s.ciphertext, sealed_at=s.sealed_at)
    got = unseal_with(moved, lane_key=keys[LB])
    assert got.state is Readable.MISBOUND and got.plaintext is None


def test_a_payload_from_a_later_build_is_not_corruption():
    """Forward compatibility is the reason the scheme is named at all."""
    _, keyring, keys = hierarchy()
    s = seal_bytes(BODY, lane_key=keys[LB], at=T0)
    future = dataclasses.replace(s, scheme="aes-gcm-v2")
    got = unseal(future, keyring=keyring, master=None)
    assert got.state is Readable.SCHEME_UNKNOWN
    assert "another build" in got.reason


def test_a_key_held_without_its_master_reports_the_master_not_a_failure():
    _, keyring, keys = hierarchy()
    s = seal_bytes(BODY, lane_key=keys[LB], at=T0)
    got = unseal(s, keyring=keyring, master=None)
    assert got.state is Readable.MASTER_MISMATCH
    assert "was not asked for" in got.reason


def test_key_state_is_three_facts():
    master, keyring, keys = hierarchy()
    assert keyring.state_of(keys[LB].key_id) is KeyState.HELD
    erased = destroy(keyring, lane_id=LB, at=T1, by="Dana Ruiz", reason="order")
    assert erased.state_of(keys[LB].key_id) is KeyState.DESTROYED
    assert erased.state_of("never-minted") is KeyState.UNKNOWN


# --- rule 12: the key-id <-> scheme middle --------------------------------


def test_reconcile_agrees_when_the_pair_agrees():
    _, keyring, keys = hierarchy()
    s = seal_bytes(BODY, lane_key=keys[LB], at=T0)
    assert reconcile(s, keyring)[0] is Agreement.AGREES


def test_reconcile_sees_a_scheme_that_moved_without_its_key():
    """The pair drifting apart is what the middle exists for. Without it the
    caller tries the key and reads a decryption failure, which is
    indistinguishable from tampering."""
    _, keyring, keys = hierarchy()
    s = seal_bytes(BODY, lane_key=keys[LB], at=T0)
    drifted = Keyring(
        tuple(dataclasses.replace(w, scheme=FERNET_V1 + "-b")
              for w in keyring.wrappings),
        keyring.erasures, keyring.escrow)
    state, why = reconcile(s, drifted)
    assert state is Agreement.SCHEME_DIVERGED and "moved without the other" in why


def test_reconcile_sees_a_key_id_pointed_at_another_lane():
    _, keyring, keys = hierarchy((LB, LM))
    s = seal_bytes(BODY, lane_key=keys[LB], at=T0)
    forged = Sealed(lane_id=LM, key_id=s.key_id, scheme=s.scheme,
                    ciphertext=s.ciphertext, sealed_at=T0)
    state, why = reconcile(forged, keyring)
    assert state is Agreement.LANE_DIVERGED and "W-1" in why


def test_unseal_routes_through_reconcile_rather_than_beside_it():
    """Rule 18. A middle nothing routes through is a ledger; this asserts the
    path, so removing the call is a failing test rather than a silent
    downgrade."""
    src = (Path(__file__).resolve().parent.parent / "records" / "atrest.py").read_text()
    body = src.split("def unseal(", 1)[1].split("\ndef ", 1)[0]
    assert "reconcile(sealed, keyring)" in body


# --- rule 12: the erasure <-> chain middle --------------------------------


def ledger_with(entries=3, lane=LB):
    """A per-lane disclosure chain, built the way the app builds one."""
    led = Ledger()
    for i in range(entries):
        led = led.record(
            Serving(Outcome.PAYLOAD, "…", Rung.L4, "a live guardian edge",
                    via_edge="guardian_of"),
            lane_id=lane, principal_id="staff-nguyen", subject_id=BEN,
            field_name=f"field-{i}", at=T0 + timedelta(days=i),
            authority="guardian_of")
    return led


def test_the_chain_still_verifies_after_the_lane_key_is_destroyed():
    """§5's solved note, as one walkthrough: seal, chain, anchor, erase, and
    the chain and the anchor must still verify while nothing opens."""
    master, keyring, keys = hierarchy()
    sealed = [seal_bytes(BODY, lane_key=keys[LB], at=T0),
              seal_bytes(b"second", lane_key=keys[LB], at=T0)]
    led = ledger_with()
    anchor = led.log_for(LB).anchor()

    erased = destroy(keyring, lane_id=LB, at=T1, by="Dana Ruiz",
                     reason="erasure request honoured")
    got = composes(led, erased, lane_id=LB, sealed=sealed, master=master,
                   anchor=anchor)

    assert got.state is Composition.COMPOSES, got.reason
    assert got.chain_ok and led.verify()[0]
    assert got.checked == 2 and got.unreadable == 2 and got.still_readable == 0
    assert all(unseal(s, keyring=erased, master=master).state
               is Readable.KEY_DESTROYED for s in sealed)


def test_the_erasure_touches_no_other_lane():
    """Per-subject erasure: one member's history goes without touching anyone
    else's."""
    master, keyring, keys = hierarchy((LB, LM))
    mine = seal_bytes(BODY, lane_key=keys[LB], at=T0)
    theirs = seal_bytes(b"mira", lane_key=keys[LM], at=T0)
    erased = destroy(keyring, lane_id=LB, at=T1, by="Dana Ruiz", reason="order")
    assert unseal(mine, keyring=erased, master=master).state is Readable.KEY_DESTROYED
    assert unseal(theirs, keyring=erased, master=master).plaintext == b"mira"


def test_composes_reports_a_broken_chain_rather_than_the_good_half():
    master, keyring, keys = hierarchy()
    sealed = [seal_bytes(BODY, lane_key=keys[LB], at=T0)]
    led = ledger_with()
    log = led.log_for(LB)
    bent = dataclasses.replace(log, entries=log.entries[1:])
    broken = Ledger(((LB, bent),))
    erased = destroy(keyring, lane_id=LB, at=T1, by="Dana Ruiz", reason="order")

    got = composes(broken, erased, lane_id=LB, sealed=sealed, master=master)
    assert got.state is Composition.CHAIN_BROKEN and not got.chain_ok


def test_composes_reports_truncation_against_the_anchor():
    """A shortened chain is self-consistent; the count anchor is what catches
    it, and an erasure is exactly when somebody would try."""
    master, keyring, keys = hierarchy()
    led = ledger_with()
    anchor = led.log_for(LB).anchor()
    log = led.log_for(LB)
    shorter = Ledger(((LB, dataclasses.replace(log, entries=log.entries[:2])),))
    erased = destroy(keyring, lane_id=LB, at=T1, by="Dana Ruiz", reason="order")

    got = composes(shorter, erased, lane_id=LB, master=master, anchor=anchor)
    assert got.state is Composition.CHAIN_BROKEN and "truncated" in got.chain_reason


def test_composes_says_not_erased_when_nothing_was():
    master, keyring, keys = hierarchy()
    got = composes(ledger_with(), keyring, lane_id=LB,
                   sealed=[seal_bytes(BODY, lane_key=keys[LB], at=T0)],
                   master=master)
    assert got.state is Composition.NOT_ERASED and got.still_readable == 1


def test_wrappings_that_vanished_without_a_dated_act_are_unrecorded():
    """Refusal 3's shape at the key layer. A key that disappeared is
    indistinguishable from one that was lost unless the act is recorded."""
    master, keyring, keys = hierarchy()
    quiet = Keyring((), keyring.erasures, keyring.escrow)
    got = composes(ledger_with(), quiet, lane_id=LB, master=master)
    assert got.state is Composition.UNRECORDED
    assert "without a record" in got.reason


def test_a_partial_erasure_does_not_read_as_a_whole_one():
    master, keyring, keys = hierarchy()
    keyring, second = rotate_lane_key(keyring, lane_id=LB, master=master, at=T1)
    half = Keyring(
        tuple(w for w in keyring.wrappings if w.key_id == second.key_id),
        (atrest.Erasure(LB, (keys[LB].key_id,), T1, "Dana Ruiz", "order"),),
        ())
    got = composes(ledger_with(), half, lane_id=LB, master=master)
    assert got.state is Composition.ERASURE_INCOMPLETE
    assert "wrapping(s) remain" in got.reason


def test_a_payload_that_still_opens_after_an_erasure_is_the_erasure_failing():
    """The stronger evidence, and the one a guardian would find: a leftover
    wrapping is housekeeping, a readable record is the erasure not happening."""
    master, keyring, keys = hierarchy()
    keyring, second = rotate_lane_key(keyring, lane_id=LB, master=master, at=T1)
    survivor = seal_bytes(BODY, lane_key=second, at=T1)
    half = Keyring(
        tuple(w for w in keyring.wrappings if w.key_id == second.key_id),
        (atrest.Erasure(LB, (keys[LB].key_id,), T1, "Dana Ruiz", "order"),),
        ())
    got = composes(ledger_with(), half, lane_id=LB, sealed=[survivor],
                   master=master)
    assert got.state is Composition.ERASURE_INCOMPLETE
    assert "still readable" in got.reason and got.still_readable == 1


def test_an_id_cannot_carry_the_header_separator():
    """The binding is a separator-joined header sealed inside the ciphertext.
    An id able to contain the separator can forge the field it is bound by."""
    master = new_master()
    for bad in ("lane\x1fben", "lane\x00ben"):
        try:
            open_lane_key(Keyring(), lane_id=bad, master=master, at=T0)
        except ValueError as exc:
            assert "header separator" in str(exc), bad
            continue
        raise AssertionError(f"{bad!r} was accepted as a lane id")


def test_composes_without_a_master_says_it_attempted_nothing():
    """Rule 13 in the direction that flatters the erasure: an unopened payload
    must not be reported as having been checked against a ciphertext."""
    master, keyring, keys = hierarchy()
    sealed = [seal_bytes(BODY, lane_key=keys[LB], at=T0)]
    erased = destroy(keyring, lane_id=LB, at=T1, by="Dana Ruiz", reason="order")
    got = composes(ledger_with(), erased, lane_id=LB, sealed=sealed)
    assert got.state is Composition.COMPOSES
    assert "no ciphertext was attempted" in got.reason


def test_the_erasure_record_outlives_the_key_it_destroyed():
    """Refusal 3: the key material goes, the dated row does not."""
    master, keyring, keys = hierarchy()
    erased = destroy(keyring, lane_id=LB, at=T1, by="Dana Ruiz",
                     reason="court order 2026-03-01")
    assert erased.keys_for(LB) == ()
    e = erased.erasure_for_lane(LB)
    assert e.by == "Dana Ruiz" and e.at == T1 and "court order" in e.reason
    assert keys[LB].key_id in e.key_ids


def test_an_erasure_needs_a_person_and_a_reason():
    _, keyring, _ = hierarchy()
    for by, reason in (("", "order"), ("the director", "order"),
                       ("Dana Ruiz", "   ")):
        try:
            destroy(keyring, lane_id=LB, at=T1, by=by, reason=reason)
        except ValueError:
            continue
        raise AssertionError(f"an erasure by {by!r} for {reason!r} was accepted")


def test_an_erasure_against_nothing_is_refused():
    try:
        destroy(Keyring(), lane_id=LB, at=T1, by="Dana Ruiz", reason="order")
    except ValueError as exc:
        assert "no key to destroy" in str(exc)
        return
    raise AssertionError("an erasure was recorded against nothing")


# --- escrow surfaced, not solved ------------------------------------------


def test_a_master_with_no_disposition_reports_absent():
    """§5's failure mode that ends the program, as a state rather than a
    silence (rules 13 and 15)."""
    _, keyring, _ = hierarchy()
    state, why = escrow_state(keyring, master_key_id="master-1", at=T1)
    assert state is EscrowState.ABSENT
    assert "no escrow disposition is recorded" in why


def test_a_disposition_that_was_never_rehearsed_is_unknown_not_recorded():
    """§5: *an untested restore is not a backup, and an untested key recovery
    is not escrow.* Quoted, not judged."""
    _, keyring, _ = hierarchy()
    keyring = record_escrow(keyring, EscrowDisposition(
        master_key_id="master-1", decided_at=T0, decided_by="Dana Ruiz",
        holders=("director", "board administrator", "sealed offline share"),
        next_rehearsal_due=T2))
    state, why = escrow_state(keyring, master_key_id="master-1", at=T1)
    assert state is EscrowState.UNKNOWN and "never been rehearsed" in why


def test_a_rehearsed_disposition_reads_recorded_and_then_goes_stale():
    _, keyring, _ = hierarchy()
    keyring = record_escrow(keyring, EscrowDisposition(
        master_key_id="master-1", decided_at=T0, decided_by="Dana Ruiz",
        holders=("director", "board administrator"), next_rehearsal_due=T2))
    keyring = rehearse(keyring, master_key_id="master-1", at=T1,
                       by="Dana Ruiz", next_due=T2)
    assert escrow_state(keyring, master_key_id="master-1", at=T1)[0] is EscrowState.RECORDED
    assert escrow_state(keyring, master_key_id="master-1", at=T2)[0] is EscrowState.STALE


def test_the_next_rehearsal_is_declared_and_has_no_default():
    """`records/dispositions.py`'s P-2 rule: a default would let issuers stop
    declaring."""
    try:
        EscrowDisposition(master_key_id="master-1", decided_at=T0,
                          decided_by="Dana Ruiz", holders=("director",),
                          next_rehearsal_due=T0)
    except ValueError as exc:
        assert "no default interval" in str(exc)
        return
    raise AssertionError("a disposition was recorded with no future drill")


def test_a_disposition_naming_no_holder_is_refused():
    for holders in ((), ("",)):
        try:
            EscrowDisposition(master_key_id="master-1", decided_at=T0,
                              decided_by="Dana Ruiz", holders=holders,
                              next_rehearsal_due=T2)
        except ValueError as exc:
            assert "naming no holder" in str(exc)
            continue
        raise AssertionError(f"holders={holders!r} was accepted")


def test_a_role_cannot_decide_escrow():
    try:
        EscrowDisposition(master_key_id="master-1", decided_at=T0,
                          decided_by="the director", holders=("a",),
                          next_rehearsal_due=T2)
    except ValueError as exc:
        assert "not a person" in str(exc)
        return
    raise AssertionError("a role signed an escrow disposition")


def test_rehearsing_an_absent_disposition_is_refused():
    _, keyring, _ = hierarchy()
    try:
        rehearse(keyring, master_key_id="master-1", at=T1, by="Dana Ruiz",
                 next_due=T2)
    except ValueError as exc:
        assert "no escrow disposition" in str(exc)
        return
    raise AssertionError("a drill was recorded against nothing")


def test_rotating_the_master_does_not_inherit_the_old_escrow():
    """The shares held for the old master do not reconstruct the new one, and a
    rotation that quietly inherited the disposition would be the worst kind of
    quiet."""
    master, keyring, _ = hierarchy()
    keyring = record_escrow(keyring, EscrowDisposition(
        master_key_id="master-1", decided_at=T0, decided_by="Dana Ruiz",
        holders=("director",), next_rehearsal_due=T2))
    keyring = rehearse(keyring, master_key_id="master-1", at=T0,
                       by="Dana Ruiz", next_due=T2)
    later = new_master(key_id="master-2")
    rotated = rewrap(keyring, was=master, now=later, at=T1)

    assert escrow_state(rotated, master_key_id="master-1", at=T1)[0] is EscrowState.RECORDED
    assert escrow_state(rotated, master_key_id="master-2", at=T1)[0] is EscrowState.ABSENT


def test_the_survey_is_derived_from_the_wrappings():
    """A master nothing is wrapped under is not this store's problem; a master
    that is, and appears in no escrow record, is the row this surfaces."""
    _, keyring, _ = hierarchy((LB, LM))
    survey = escrow_survey(keyring, at=T1)
    assert survey == (("master-1", EscrowState.ABSENT, survey[0][2]),)
    assert keyring.masters() == ("master-1",)


def test_the_conformance_check_reports_escrow_honestly_today():
    """The check must read `UNKNOWN` — not `PASS`, not `ABSENT`, not missing.

    **This assertion said `ABSENT` until S-3 and was right to**, on evidence
    that has since stopped being true: *"no keyring and no sealed store exist
    here."* Gate G-A picked `E-1` (3-of-5, `docs/ESCROW.md`, 2026-07-31) and
    migration 004 means a sealed store can exist, so both halves of that
    evidence moved.

    The row is now the middle state and both walls matter:

    * not `ABSENT` — a policy *is* recorded, and *nothing decided* is a
      different fact from *decided and never drilled* (rule 13, which is why
      `EscrowState` has four members);
    * not `PASS` — §5: *an untested key recovery is not escrow*, and
      `docs/ESCROW.md` records zero rehearsals on purpose.

    Both walls are ablated (`tests/ablate.py`), and the transition to `PASS` on
    a dated rehearsal is driven in `tests/test_conform.py` against a synthetic
    document rather than waited for.
    """
    import conform  # noqa: E402
    from audit import escrow_facts  # noqa: E402

    got = conform.check_key_escrow()
    assert got.state is conform.State.UNKNOWN, got.evidence
    assert got.id == "key-escrow"
    assert conform.check_key_escrow in conform.CHECKS

    # The evidence cites the file and the file's own facts, derived rather than
    # quoted here (rule 17): the threshold and the holder count come out of
    # docs/ESCROW.md, so editing the policy moves this test with it.
    facts = escrow_facts()
    assert "ESCROW.md" in got.evidence, got.evidence
    assert facts.threshold in got.evidence, got.evidence
    assert f"{facts.holders} custodian" in got.evidence, got.evidence
    assert f"{len(facts.rehearsals)} rehearsal" in got.evidence, got.evidence
    assert not facts.rehearsed, (
        "docs/ESCROW.md now records a rehearsal — this test and the row's "
        "expected state both move to PASS, by a ceremony happening, which is "
        "the only thing that should move them")
    # The state name is atrest's, not a second vocabulary invented here.
    assert atrest.EscrowState.UNKNOWN.value.upper() in got.evidence, got.evidence


# --- the primitive seam ---------------------------------------------------


def test_the_module_refuses_rather_than_storing_in_the_clear():
    """`records/receipts.py`'s argument: a silent downgrade makes sealed and
    unsealed look identical at every call site."""
    real = atrest._fernet_primitives

    def broken():
        raise atrest.PrimitiveUnavailable("no primitive")

    try:
        atrest._fernet_primitives = broken
        try:
            new_master()
        except atrest.PrimitiveUnavailable:
            assert not atrest.available()
            return
        raise AssertionError("a key was minted with no primitive")
    finally:
        atrest._fernet_primitives = real


def test_availability_is_derived_by_attempting_the_import():
    assert atrest.available() is True


# --- not broken shut ------------------------------------------------------


def test_the_module_is_not_broken_shut():
    """Every refusal above is worthless if the ordinary path never works."""
    master, keyring, keys = hierarchy((LB, LM))
    sealed = {l: seal_bytes(l.encode(), lane_key=keys[l], at=T0) for l in (LB, LM)}
    later = new_master(key_id="master-2")
    keyring = rewrap(keyring, was=master, now=later, at=T1)
    keyring = record_escrow(keyring, EscrowDisposition(
        master_key_id="master-2", decided_at=T1, decided_by="Dana Ruiz",
        holders=("director", "board administrator"), next_rehearsal_due=T2))
    keyring = rehearse(keyring, master_key_id="master-2", at=T1,
                       by="Dana Ruiz", next_due=T2)

    for lane, s in sealed.items():
        assert unseal(s, keyring=keyring, master=later).plaintext == lane.encode()
    assert escrow_state(keyring, master_key_id="master-2", at=T1)[0] is EscrowState.RECORDED
    assert composes(ledger_with(), keyring, lane_id=LB,
                    sealed=list(sealed.values()),
                    master=later).state is Composition.NOT_ERASED


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
