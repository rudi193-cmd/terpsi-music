"""§18 item 5: what actually leaves at the exit, in a form nobody needs this app to read.

§11.1 sets the test and it is the fleet's, not this document's:

> *"Sovereignty is the ability to leave… **if an exit line cannot be written
> honestly, the app does not get listed.**"*

`records/exit.py` decides *what* transfers at W-6's threshold. This turns that
decision into bytes a person can open. They are different jobs and the second is
where the promise is usually broken — a system can compute a perfect transfer and
hand over a proprietary dump.

**Nothing here touches the filesystem, and that is deliberate.** `bundle()`
returns `(name, media type, text)` and the caller writes. §6's core/seam
partition is the reason — the core is import-pure and a module that opens files
is a write path nothing has declared (`tools/conform.py` checks for exactly
this). It also makes the export testable without a temp directory, which is why
`witness.py` opens no socket for the same argument.

**The format is chosen against the five-point test, not for convenience.**

* **CSV and plain text.** Not JSON, not a pickle, not this repository's schema.
  A guardian opens `entries.csv` in whatever they have; a lawyer prints
  `README.txt`. *"Data readable without the app"* fails the moment the recipient
  needs a parser we shipped.
* **The exit terms travel with the data**, in the first file, in the words
  written when the lane was opened. A recipient holding rows and no statement of
  what they were promised has the data and not the exit.
* **A manifest with per-file digests and a count.** The truncation problem
  again: a bundle with a file quietly missing looks like a smaller bundle.
  `MANIFEST.txt` is what `witness.py`'s anchor is to the log.

**Full history, unfiltered.** W-6 is explicit — *an agent retired is retired
**with** its record* — so nothing is dropped by rung on the way out. `L5` is the
one thing that never renders to anyone, and a lane's `L5` rows are enforcement
material rather than the subject's record; if one ever reaches here it is
reported in the manifest as withheld **by name and count**, never silently
omitted. A quiet drop is how a "safe subset" export gets built by accident.

Stdlib only. No network, no filesystem.
"""

from __future__ import annotations

import csv
import hashlib
import io
from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

from .rungs import NEVER_SERVED


@dataclass(frozen=True)
class Artifact:
    """One file in the bundle. The caller writes it; this never does."""

    name: str
    media_type: str
    text: str

    @property
    def digest(self) -> str:
        return hashlib.sha256(self.text.encode("utf-8")).hexdigest()


def _served(transfer) -> list:
    """The rows entries.csv carries: everything except the never-rendered L5.

    One definition, because `bundle()` and `_readme()` both need it and two
    copies of *which rung never leaves* is the pair rule 12 exists to forbid —
    and, concretely, two identical lines made the ablation that targets this
    filter match two sites.
    """
    return [e for e in transfer.entries if getattr(e, "rung", None) is not NEVER_SERVED]


def _rows(entries: Sequence) -> Tuple[Tuple[str, ...], Tuple[Tuple[str, ...], ...]]:
    """Flatten whatever the lane held into a table with a stable header.

    Deliberately duck-typed. The lane's contents are the domain's business and
    this module's job is to render them; a serializer that only handled the
    three types that existed on the day it was written would silently drop the
    fourth.
    """
    header = ("field", "rung", "category", "value", "provenance")
    out = []
    for e in entries:
        out.append((
            str(getattr(e, "name", "") or getattr(e, "field_name", "")),
            str(getattr(e, "rung", "") or ""),
            str(getattr(e, "category", "") or ""),
            str(getattr(e, "payload", "") if getattr(e, "payload", None) is not None
                else getattr(e, "instruction", "") or ""),
            str(getattr(e, "provenance", "") or ""),
        ))
    return header, tuple(out)


def _csv(header: Sequence[str], rows: Sequence[Sequence[str]]) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(header)
    w.writerows(rows)
    return buf.getvalue()


def _readme(transfer) -> str:
    withheld = [e for e in transfer.entries if getattr(e, "rung", None) is NEVER_SERVED]
    # entries.csv holds the *served* rows, not every entry: the withheld ones are
    # named in MANIFEST.txt and never rendered. The truncation self-check has to
    # count against what the file actually contains, or a bundle with any
    # withheld record fails its own check — the CSV legitimately has fewer rows
    # than the total, and a recipient told "fewer than the total means missing"
    # reads a correct export as a truncated one.
    served = _served(transfer)
    lines = [
        "YOUR RECORD",
        "===========",
        "",
        f"This is the record {_recipient(transfer)} kept about "
        f"{transfer.to_whom}, handed over on "
        f"{transfer.at.date().isoformat()} at {transfer.threshold.value}.",
        "",
        "WHAT YOU WERE PROMISED",
        "----------------------",
        "These are the exit terms written down on the day the record was opened,",
        "in the words used then:",
        "",
        f"    {transfer.exit_terms}",
        "",
        "WHAT IS IN THIS FOLDER",
        "----------------------",
        "  entries.csv   every record held, one row each. Open it in any",
        "                spreadsheet. Nothing has been removed by category.",
        "  MANIFEST.txt  a list of these files with a checksum and a count,",
        "                so you can tell whether anything went missing.",
        "  README.txt    this file.",
        "",
        f"entries.csv has {len(served)} record(s), one per row. If it has fewer",
        "rows than that, some were lost after the bundle was made, and",
        "MANIFEST.txt's checksums are how you tell which.",
        "",
    ]
    if withheld:
        lines += [
            f"({len(served)} shown here plus {len(withheld)} withheld below is "
            f"{len(transfer.entries)} on record in total.)",
            "",
        ]
    if withheld:
        lines += [
            "WITHHELD",
            "--------",
            f"{len(withheld)} record(s) are named in MANIFEST.txt but not included:",
            "these are enforcement material (the contents of an order or a",
            "direction), which is never rendered to anyone, including you. They",
            "are listed rather than silently dropped so you know they exist.",
            "",
        ]
    lines += [
        "READING IT WITHOUT THIS SOFTWARE",
        "--------------------------------",
        "entries.csv is comma-separated text. The columns are:",
        "  field       what the record is about",
        "  rung        how sensitive it was treated as (L1 open .. L5 never shown)",
        "  category    health, money, discipline, likeness, or blank",
        "  value       the record itself",
        "  provenance  how it was known (P1 measured .. P5 assumed), or blank",
        "",
        "Nothing here requires the program's software. If you are reading this",
        "sentence, the export worked.",
        "",
    ]
    return "\n".join(lines)


def _recipient(transfer) -> str:
    return "the music program"


def _manifest(transfer, artifacts: Sequence[Artifact]) -> str:
    withheld = [e for e in transfer.entries if getattr(e, "rung", None) is NEVER_SERVED]
    lines = [
        "MANIFEST",
        "========",
        f"lane:       {transfer.lane_id}",
        f"issued to:  {transfer.to_whom}",
        f"at:         {transfer.at.isoformat()}",
        f"threshold:  {transfer.threshold.value}",
        f"records:    {len(transfer.entries)}",
        f"withheld:   {len(withheld)}",
        "",
        "FILES (sha256, bytes, name)",
    ]
    for a in artifacts:
        lines.append(f"  {a.digest}  {len(a.text.encode('utf-8')):>8}  {a.name}")
    if withheld:
        lines += ["", "WITHHELD RECORDS (named, not included)"]
        for e in withheld:
            lines.append(f"  {getattr(e, 'name', '?')}  ({e.rung}, enforcement-only)")
    lines += [
        "",
        "A file missing from this list, or a checksum that does not match, means",
        "the bundle was altered after it was made.",
        "",
    ]
    return "\n".join(lines)


def bundle(transfer) -> Tuple[Artifact, ...]:
    """Render a W-6 transfer as files. The caller writes them.

    The manifest is built last and over the *other* artifacts, so it cannot
    describe a file that is not in the bundle.
    """
    if not transfer.complete:
        raise ValueError(
            "an incomplete transfer has nothing to export; W-6 requires the "
            "record and the written exit terms"
        )
    served = _served(transfer)
    header, rows = _rows(served)
    body = (
        Artifact("README.txt", "text/plain", _readme(transfer)),
        Artifact("entries.csv", "text/csv", _csv(header, rows)),
    )
    return body + (Artifact("MANIFEST.txt", "text/plain",
                            _manifest(transfer, body)),)


def verify(artifacts: Sequence[Artifact]) -> Tuple[bool, str]:
    """Check a received bundle against its own manifest.

    The recipient's half of the exit, and the reason the manifest exists: a
    bundle that lost a file in transit is otherwise a smaller bundle.
    """
    by_name = {a.name: a for a in artifacts}
    man = by_name.get("MANIFEST.txt")
    if man is None:
        return (False, "no MANIFEST.txt; the bundle cannot check itself")
    listed = {}
    for line in man.text.splitlines():
        parts = line.split()
        if len(parts) == 3 and len(parts[0]) == 64:
            listed[parts[2]] = parts[0]
    if not listed:
        return (False, "MANIFEST.txt lists no files")
    for name, digest in sorted(listed.items()):
        got = by_name.get(name)
        if got is None:
            return (False, f"{name} is listed in the manifest and missing")
        if got.digest != digest:
            return (False, f"{name} does not match its manifest checksum")
    return (True, f"{len(listed)} file(s) present and matching")
