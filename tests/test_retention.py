"""§10's season-boundary purge, attacked. The claim is not that it erases — the
key layer already does — but that it erases **only what a boundary carried past
retention**, **never by deleting**, **never the record of its own act**, and
**never a whole student because one of their records aged out**.

The last of those was missing until 2026-08-02 and the omission had a shape
worth keeping: the isolation test here compared `lane-a` against `lane-b` and
passed, while `purge()` destroyed a live medical note the moment an unrelated
attendance record in the *same* lane came due. A lane is one student and
`atrest.destroy` drops every wrapping under it, so nothing that only ever looks
across lanes can see it. Attempting the forbidden act *within* a lane is what
these assert (§18 item 19).

Every guard here attempts the forbidden thing and asserts the refusal (rule 19,
§10 acceptance-is-mutation), and each has a mutation in `tests/ablate.py`.
Stdlib only, plus the one declared dependency the erasure path needs.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from records import atrest, retention  # noqa: E402
from records.retention import (  # noqa: E402
    Calendar, Disposition, Indelible, LaneNotDue, NoSeason, NotDue, Policy,
    Standing, UnknownKind, UnknownLane, assess, dispose, due, purge,
)

UTC = timezone.utc
FALL_END = datetime(2025, 12, 20, tzinfo=UTC)
SPRING_END = datetime(2026, 6, 1, tzinfo=UTC)
NOW_LATER = datetime(2027, 6, 1, tzinfo=UTC)     # well past a one-year horizon
NOW_SOON = datetime(2026, 1, 5, tzinfo=UTC)      # inside the horizon
LANE = "lane-benjamin"
KIND = "attendance"
HEALTH_KIND = "medical"


@dataclass(frozen=True)
class Rec:
    """A stand-in for any dated record — structurally `Retainable`, imports
    nothing from `records/`, and carries no list of students."""
    season: str
    created_at: datetime
    invalid_at: Optional[datetime] = None


def _calendar() -> Calendar:
    return Calendar({"2025-fall": FALL_END, "2026-spring": SPRING_END})


def _policy(**extra) -> Policy:
    return Policy({KIND: timedelta(days=365),
                   HEALTH_KIND: timedelta(days=3650), **extra})


def _closed(season: str = "2025-fall") -> Rec:
    return Rec(season, created_at=FALL_END, invalid_at=FALL_END)


def _live(season: str = "2025-fall") -> Rec:
    return Rec(season, created_at=FALL_END, invalid_at=None)


def _keyring_with_lane():
    master = atrest.new_master(key_id="master-1")
    keyring, key = atrest.open_lane_key(atrest.Keyring(), lane_id=LANE,
                                        master=master, at=FALL_END)
    return keyring, key, master


# --- the positive control: it actually purges, and the tombstone survives ----


def test_the_module_is_not_broken_shut():
    """A closed record past its horizon is due; disposing and purging it, in a
    lane holding nothing else, destroys the lane's key and leaves an `Erasure`
    that says why it will not open."""
    rec = _closed()
    got = due([(rec, KIND)], _calendar(), _policy(), NOW_LATER)
    assert got == ((rec, KIND),)
    d = dispose(rec, KIND, lane_id=LANE, calendar=_calendar(), policy=_policy(),
                now=NOW_LATER, by="Dana Ruiz", reason="season purge")
    keyring, key, _ = _keyring_with_lane()
    erased = purge(keyring, [d], lane_records={LANE: [(rec, KIND)]},
                   calendar=_calendar(), policy=_policy(), now=NOW_LATER)
    assert erased.state_of(key.key_id) is atrest.KeyState.DESTROYED
    survivor = erased.erasure_for_lane(LANE)
    assert survivor is not None and survivor.by == "Dana Ruiz"


# --- refusal 3 / rule 16: a purge is erasure + tombstone, never a delete -----


def test_a_purge_leaves_the_record_of_its_act_not_a_hole():
    rec = _closed()
    d = dispose(rec, KIND, lane_id=LANE, calendar=_calendar(), policy=_policy(),
                now=NOW_LATER, by="Dana Ruiz", reason="season purge")
    keyring, _key, _ = _keyring_with_lane()
    erased = purge(keyring, [d], lane_records={LANE: [(rec, KIND)]},
                   calendar=_calendar(), policy=_policy(), now=NOW_LATER)
    # The erasure row survives the thing it erased — who/when/why is still answerable.
    assert erased.erasure_for_lane(LANE) is not None


def test_the_module_never_deletes():
    """Structural: no delete/unlink/remove verb anywhere in the source. A purge
    that grew a delete path would be refusal 3 with a hole in it."""
    src = (Path(__file__).resolve().parent.parent / "records" / "retention.py").read_text()
    for verb in ("os.remove", "os.unlink", "shutil.rmtree", ".pop(", "del "):
        assert verb not in src, f"retention.py must not {verb!r} — a purge is not a delete"


def test_the_record_of_a_purge_is_not_itself_purgeable():
    d = Disposition(lane_id=LANE, season="2025-fall", kind=KIND, at=NOW_LATER,
                    by="Dana Ruiz", reason="season purge")
    for act in (
        lambda: assess(d, KIND, _calendar(), _policy(), NOW_LATER),
        lambda: dispose(d, KIND, lane_id=LANE, calendar=_calendar(),
                        policy=_policy(), now=NOW_LATER, by="x", reason="y"),
        lambda: due([(d, KIND)], _calendar(), _policy(), NOW_LATER),
    ):
        try:
            act()
        except Indelible:
            continue
        raise AssertionError("a purge disposition was accepted as retainable (rule 16)")


# --- no early purge, no purge of the living ---------------------------------


def test_a_retained_record_inside_its_horizon_is_not_due():
    rec = _closed()
    assert assess(rec, KIND, _calendar(), _policy(), NOW_SOON).standing is Standing.RETAINED
    assert due([(rec, KIND)], _calendar(), _policy(), NOW_SOON) == ()
    try:
        dispose(rec, KIND, lane_id=LANE, calendar=_calendar(), policy=_policy(),
                now=NOW_SOON, by="x", reason="early")
    except NotDue:
        return
    raise AssertionError("purged a record still inside its retention horizon")


def test_a_live_record_is_never_due():
    rec = _live()
    assert assess(rec, KIND, _calendar(), _policy(), NOW_LATER).standing is Standing.LIVE
    assert due([(rec, KIND)], _calendar(), _policy(), NOW_LATER) == ()
    try:
        dispose(rec, KIND, lane_id=LANE, calendar=_calendar(), policy=_policy(),
                now=NOW_LATER, by="x", reason="live")
    except NotDue:
        return
    raise AssertionError("purged a record still true in the world (invalid_at is None)")


# --- rule 13: absence is unknown, never a licence ---------------------------


def test_a_record_with_no_season_is_refused():
    rec = Rec("", created_at=FALL_END, invalid_at=FALL_END)
    try:
        assess(rec, KIND, _calendar(), _policy(), NOW_LATER)
    except NoSeason:
        return
    raise AssertionError("a seasonless record was placed on the retention axis")


def test_an_unknown_kind_fails_closed():
    rec = _closed()
    try:
        assess(rec, "inventory", _calendar(), _policy(), NOW_LATER)
    except UnknownKind:
        return
    raise AssertionError("a kind with no policy horizon was given a default retention")


def test_an_unplaceable_season_is_unknown_not_due():
    rec = _closed("2099-fall")            # not in the calendar
    a = assess(rec, KIND, _calendar(), _policy(), NOW_LATER)
    assert a.standing is Standing.UNKNOWN
    assert due([(rec, KIND)], _calendar(), _policy(), NOW_LATER) == ()


def test_a_naive_season_end_is_refused():
    try:
        Calendar({"2025-fall": datetime(2025, 12, 20)})   # no tzinfo
    except ValueError:
        return
    raise AssertionError("a season boundary without a timezone was accepted")


def test_a_naive_now_is_refused_not_crashed():
    """A naive `now` gets the same clean refusal `Calendar` gives a naive
    season-end — a plain `ValueError`, not a bare `TypeError` from comparing
    across timezone-awareness deep in `assess`."""
    try:
        assess(_closed(), KIND, _calendar(), _policy(), datetime(2027, 6, 1))
    except ValueError:
        return
    raise AssertionError("a naive `now` was compared against a boundary (crash, not refusal)")


def test_a_naive_invalid_at_is_refused_not_crashed():
    rec = Rec("2025-fall", created_at=FALL_END, invalid_at=datetime(2025, 12, 20))
    try:
        assess(rec, KIND, _calendar(), _policy(), NOW_LATER)
    except ValueError:
        return
    raise AssertionError("a naive `invalid_at` was compared against a boundary (crash, not refusal)")


# --- rule 15: a purge is dated and attributed -------------------------------


def test_purge_will_not_drive_a_bare_lane_id():
    keyring, _key, _ = _keyring_with_lane()
    try:
        purge(keyring, [LANE],            # a string, not a dated Disposition
              lane_records={LANE: [(_closed(), KIND)]}, calendar=_calendar(),
              policy=_policy(), now=NOW_LATER)
    except TypeError:
        return
    raise AssertionError("purge() erased from a bare lane id with no dated record (rule 15)")


def test_a_disposition_without_attribution_or_reason_is_refused():
    for by, reason in (("", "r"), ("who", "")):
        try:
            Disposition(lane_id=LANE, season="2025-fall", kind=KIND,
                        at=NOW_LATER, by=by, reason=reason)
        except ValueError:
            continue
        raise AssertionError("an unattributed or unreasoned purge was accepted (rule 15)")


# --- the named middle (rule 12): purge touches only what due() named --------


def test_purge_destroys_only_the_lanes_it_was_given():
    master = atrest.new_master(key_id="master-1")
    kr = atrest.Keyring()
    kr, key_a = atrest.open_lane_key(kr, lane_id="lane-a", master=master, at=FALL_END)
    kr, key_b = atrest.open_lane_key(kr, lane_id="lane-b", master=master, at=FALL_END)
    aged = _closed()
    d = dispose(aged, KIND, lane_id="lane-a", calendar=_calendar(),
                policy=_policy(), now=NOW_LATER, by="Dana Ruiz", reason="purge")
    erased = purge(kr, [d],
                   lane_records={"lane-a": [(aged, KIND)],
                                 "lane-b": [(_live(), KIND)]},
                   calendar=_calendar(), policy=_policy(), now=NOW_LATER)
    assert erased.state_of(key_a.key_id) is atrest.KeyState.DESTROYED
    assert erased.state_of(key_b.key_id) is atrest.KeyState.HELD


# --- rule 8: a record's disposition does not reach the whole student ---------
#
# The isolation test above compares one lane against another and passes on code
# that erases a live medical note the moment an unrelated attendance record ages
# out, because the forbidden act is *inside* a lane and nothing was pointed at
# it. These are that assertion.


def _lane_holding(*records):
    """A lane with one aged-out attendance record and whatever else is passed —
    the ordinary shape of a student, which is what makes the defect ordinary."""
    aged = _closed()
    master = atrest.new_master(key_id="master-1")
    kr, key = atrest.open_lane_key(atrest.Keyring(), lane_id=LANE,
                                   master=master, at=FALL_END)
    note = atrest.seal_bytes(b"epi-pen in the case", lane_key=key, at=FALL_END)
    d = dispose(aged, KIND, lane_id=LANE, calendar=_calendar(),
                policy=_policy(), now=NOW_LATER, by="Dana Ruiz",
                reason="season purge")
    held = [(aged, KIND)] + [(r, k) for r, k in records]
    return kr, key, master, note, d, held


def test_a_live_sibling_in_the_same_lane_survives_a_due_records_purge():
    """**The one that was missing.** Purging a due attendance record must not
    destroy the key opening a live medical note in the same lane — a lane is one
    student, and `atrest.destroy` drops every wrapping under it. The payload is
    read back, not merely reported held: `KEY_DESTROYED` is what this asserted
    against, and only a plaintext proves the erasure did not reach it."""
    kr, key, master, note, d, held = _lane_holding(
        (Rec("2026-spring", created_at=FALL_END), HEALTH_KIND))
    try:
        purge(kr, [d], lane_records={LANE: held}, calendar=_calendar(),
              policy=_policy(), now=NOW_LATER)
    except LaneNotDue:
        opened = atrest.unseal(note, keyring=kr, master=master)
        assert kr.state_of(key.key_id) is atrest.KeyState.HELD
        assert opened.state is atrest.Readable.OPENED, opened.reason
        assert opened.plaintext == b"epi-pen in the case"
        return
    raise AssertionError(
        "a due attendance record's purge destroyed the key of a live health "
        "record in the same lane (rule 8: one lane is one student)")


def test_every_not_due_standing_blocks_the_lane_not_only_the_live_one():
    """`RETAINED` and `UNKNOWN` are kept for the same reason `LIVE` is — `due()`
    returns none of them — so a lane holding any of the three is refused. A
    guard that only saw `LIVE` would erase a closed record still inside its
    horizon and one whose season the calendar cannot place."""
    siblings = {
        Standing.LIVE: Rec("2026-spring", created_at=FALL_END),
        Standing.RETAINED: Rec("2026-spring", created_at=FALL_END,
                               invalid_at=SPRING_END),
        Standing.UNKNOWN: Rec("2099-fall", created_at=FALL_END,
                              invalid_at=FALL_END),
    }
    for standing, sibling in siblings.items():
        assert assess(sibling, HEALTH_KIND, _calendar(), _policy(),
                      NOW_LATER).standing is standing
        kr, key, _master, _note, d, held = _lane_holding((sibling, HEALTH_KIND))
        try:
            purge(kr, [d], lane_records={LANE: held}, calendar=_calendar(),
                  policy=_policy(), now=NOW_LATER)
        except LaneNotDue:
            continue
        raise AssertionError(
            f"a lane holding a {standing.value} record was erased whole")


def test_a_lane_the_caller_cannot_enumerate_is_not_purged():
    """Rule 13, on the widest act in the module: a caller who cannot list the
    lane gets a refusal, not an erasure of everything in it. Both absences are
    attempted — the lane missing from the mapping, and the lane listed as
    holding nothing — because either one alone leaves the other as a way past
    `LaneNotDue` that needs no argument at all."""
    for lane_records in ({}, {LANE: []}, {"lane-somebody-else": []}):
        kr, key, _master, _note, d, _held = _lane_holding()
        try:
            purge(kr, [d], lane_records=lane_records, calendar=_calendar(),
                  policy=_policy(), now=NOW_LATER)
        except UnknownLane:
            assert kr.state_of(key.key_id) is atrest.KeyState.HELD
            continue
        raise AssertionError(
            f"a lane enumerated as {lane_records!r} was erased whole; an "
            "unenumerable lane is unknown, not empty (rule 13)")


def test_purge_cannot_be_asked_to_skip_the_lane_check():
    """The refusal is an absent ability, not a withheld permission
    (`docs/CROSSINGS.md`, crossing one). There is no argument that turns it off
    and no default that stands in for the lane's records: a caller who does not
    supply them does not get a purge, it gets a `TypeError` from the signature."""
    kr, key, _master, _note, d, _held = _lane_holding()
    try:
        purge(kr, [d])
    except TypeError:
        assert kr.state_of(key.key_id) is atrest.KeyState.HELD
        return
    raise AssertionError(
        "purge() erased a lane without being shown what the lane holds")


# --- rule 12: the middle for the pair this created --------------------------


def test_the_open_item_and_the_refusal_do_not_drift():
    """§18 item 19 declares what `purge()` refuses; `records/retention.py`
    enforces it. That is a declaration and an enforcement in two files, which is
    a pair, and a pair with no middle is how a document comes to describe a
    guard the code moved past — §18 item 6 found exactly that in this
    repository's own note about counts.

    This is the narrow middle and it is worth saying what it does *not* do: it
    cannot check that the prose is true, only that the exceptions the item leans
    on are the ones the module actually raises. Renaming a refusal without
    touching the item, or citing one that was never written, fails here."""
    item = (ROOT / "docs" / "ARCHITECTURE.md").read_text(encoding="utf-8")
    start = item.index("**19 · The seal is per lane")
    item = item[start:item.index("\n### ", start)]
    src = (ROOT / "records" / "retention.py").read_text(encoding="utf-8")
    named = {n for n in ("LaneNotDue", "UnknownLane") if f"`{n}`" in item}
    assert named == {"LaneNotDue", "UnknownLane"}, (
        f"§18 item 19 names {sorted(named)}; the lane-scope refusal is both, "
        "and an item citing one of them describes half a guard")
    for name in sorted(named):
        assert hasattr(retention, name), f"§18 item 19 names {name}, which does not exist"
        assert f"raise {name}(" in src, (
            f"§18 item 19 says {name} is raised; nothing in retention.py raises it")


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
