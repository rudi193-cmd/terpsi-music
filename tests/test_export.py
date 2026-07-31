"""§18 item 5: the bundle a graduate can read without this software.

Stdlib only. Runs under pytest or directly.
"""

from __future__ import annotations

import csv
import io
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import dataclasses  # noqa: E402

from records import Field, Rung  # noqa: E402
from records.exit import Threshold, open_lane, transfer  # noqa: E402
from records.export import Artifact, bundle, verify  # noqa: E402

T0, T9 = datetime(2022, 8, 1), datetime(2026, 6, 1)
BEN, LB = "student-ben", "lane-ben"
TERMS = ("At graduation, keys and full history issue to Ben; guardian standing "
         "ends on the same date.")


def lane():
    return open_lane(LB, BEN, at=T0, threshold=Threshold.GRADUATION,
                     exit_terms=TERMS)


def history(with_l5=False):
    h = [
        Field(LB, BEN, "chair", Rung.L3, payload="trumpet 2", provenance="P1"),
        Field(LB, BEN, "allergy", Rung.L4, category="health", payload="tree nut"),
        Field(LB, BEN, "balance", Rung.L4, category="money", payload="$0.00"),
    ]
    if with_l5:
        h.append(Field(LB, BEN, "restriction_contents", Rung.L5, category="legal",
                       payload="findings"))
    return h


def made(**kw):
    return bundle(transfer(lane(), entries=history(**kw), edges=[], at=T9))


def named(arts, name):
    return next(a for a in arts if a.name == name)


# --- readable without this software ---------------------------------------


def test_the_bundle_is_csv_and_plain_text_and_nothing_else():
    """*"Data readable without the app"* fails the moment the recipient needs a
    parser we shipped."""
    arts = made()
    assert {a.name for a in arts} == {"README.txt", "entries.csv", "MANIFEST.txt"}
    assert {a.media_type for a in arts} == {"text/plain", "text/csv"}


def test_the_csv_parses_with_the_stdlib_reader_and_has_a_header():
    rows = list(csv.reader(io.StringIO(named(made(), "entries.csv").text)))
    assert rows[0] == ["field", "rung", "category", "value", "provenance"]
    assert {r[0] for r in rows[1:]} == {"chair", "allergy", "balance"}


def test_the_exit_terms_travel_with_the_data_in_the_words_written_at_opening():
    """A recipient holding rows and no statement of what they were promised has
    the data and not the exit."""
    assert TERMS in named(made(), "README.txt").text


def test_the_readme_says_how_many_records_there_should_be():
    """The truncation problem, addressed to a person rather than to a verifier."""
    text = named(made(), "README.txt").text
    assert "There are 3 records" in text
    assert "you did not receive all of it" in text


# --- full history, unfiltered (W-6) ---------------------------------------


def test_nothing_is_dropped_by_rung_on_the_way_out():
    """*"An agent retired is retired **with** its record."* A safe-subset export
    is the thing W-6 exists to forbid."""
    rows = list(csv.reader(io.StringIO(named(made(), "entries.csv").text)))[1:]
    assert {r[1] for r in rows} == {"L3", "L4"}
    assert any("tree nut" in r[3] for r in rows), "an L4 health payload was withheld"


def test_an_L5_record_is_named_and_counted_never_silently_dropped():
    """The one exception, and it is reported. A quiet drop is how a safe-subset
    export gets built by accident."""
    arts = made(with_l5=True)
    rows = list(csv.reader(io.StringIO(named(arts, "entries.csv").text)))[1:]
    assert "findings" not in named(arts, "entries.csv").text
    man = named(arts, "MANIFEST.txt").text
    assert "withheld:   1" in man and "restriction_contents" in man
    assert "WITHHELD" in named(arts, "README.txt").text


def test_a_lane_with_no_L5_says_withheld_zero_rather_than_staying_silent():
    assert "withheld:   0" in named(made(), "MANIFEST.txt").text


# --- the manifest ---------------------------------------------------------


def test_the_manifest_lists_every_other_file_with_a_checksum():
    arts = made()
    man = named(arts, "MANIFEST.txt").text
    for a in arts:
        if a.name == "MANIFEST.txt":
            continue
        assert a.digest in man and a.name in man


def test_the_manifest_cannot_describe_a_file_that_is_not_in_the_bundle():
    """Built last and over the other artifacts, so the two cannot disagree."""
    arts = made()
    man = named(arts, "MANIFEST.txt").text
    listed = {p[2] for p in (l.split() for l in man.splitlines())
              if len(p) == 3 and len(p[0]) == 64}
    assert listed == {a.name for a in arts if a.name != "MANIFEST.txt"}


def test_a_bundle_that_lost_a_file_in_transit_fails_verification():
    """Otherwise it is just a smaller bundle."""
    arts = made()
    assert verify(arts)[0]
    short = tuple(a for a in arts if a.name != "entries.csv")
    ok, why = verify(short)
    assert not ok and "missing" in why


def test_an_altered_file_fails_verification():
    arts = made()
    tampered = tuple(
        dataclasses.replace(a, text=a.text.replace("trumpet 2", "trumpet 1"))
        if a.name == "entries.csv" else a
        for a in arts)
    ok, why = verify(tampered)
    assert not ok and "checksum" in why


def test_a_bundle_with_no_manifest_cannot_check_itself():
    ok, why = verify(tuple(a for a in made() if a.name != "MANIFEST.txt"))
    assert not ok and "cannot check itself" in why


# --- the core writes nothing ----------------------------------------------


def test_this_module_never_touches_the_filesystem():
    """§6's core/seam partition. A module that opens files is a write path
    nothing has declared, and `tools/conform.py` checks for exactly this."""
    src = (Path(__file__).resolve().parent.parent / "records" / "export.py").read_text()
    body = src.split('"""', 2)[-1]
    for banned in ("open(", "write_text", "write_bytes", "Path(", "os.", "shutil"):
        assert banned not in body, f"records/export.py reaches the filesystem: {banned}"


def test_an_incomplete_transfer_exports_nothing():
    t = transfer(lane(), entries=history(), edges=[], at=T9)
    empty = dataclasses.replace(t, entries=())
    try:
        bundle(empty)
    except ValueError as exc:
        assert "incomplete" in str(exc)
        return
    raise AssertionError("an incomplete transfer produced a bundle")


def test_the_module_is_not_broken_shut():
    arts = made()
    assert verify(arts)[0] and len(arts) == 3
    assert all(a.text.strip() for a in arts)


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
